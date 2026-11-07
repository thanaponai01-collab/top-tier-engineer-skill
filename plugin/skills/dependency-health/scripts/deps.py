"""deps.py - list what a repo's dependencies owe, and refuse "done" while something high is undecided.

    python deps.py <repo>                              findings -> .deps/findings.md
    python deps.py <repo> --run "CMD"                  also record manifests, lockfiles and tests
    python deps.py <repo> --accept ID --reason TEXT --until YYYY-MM-DD   accept one on purpose
    python deps.py <repo> --done [--run "CMD"]         check, save .deps/history.json, DEPS: done

Known holes come from --advisories FILE, else OSV.dev (skipped with --offline). An ecosystem whose
holes could not be checked is listed under "Not checked", never reported healthy.
"""
import argparse, ast, datetime, hashlib, json, os, re, subprocess, sys, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams  # noqa: E402

STATE = ".deps"
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "__pycache__", "site-packages", STATE,
             "dist", "build", ".tox", ".mypy_cache", ".pytest_cache"}
TESTS_RAN = re.compile(r"Ran (\d+) tests?|(\d+) passed|Tests:\s+(\d+) passed")
OSV = "https://api.osv.dev/v1/querybatch"
# Published end-of-life dates (python.org/downloads, nodejs.org/about/previous-releases).
EOL = {
    "python": {"2.7": "2020-01-01", "3.5": "2020-09-13", "3.6": "2021-12-23", "3.7": "2023-06-27",
               "3.8": "2024-10-07", "3.9": "2025-10-31", "3.10": "2026-10-31", "3.11": "2027-10-31",
               "3.12": "2028-10-31", "3.13": "2029-10-31", "3.14": "2030-10-31"},
    "node": {"10": "2021-04-30", "12": "2022-04-30", "14": "2023-04-30", "15": "2021-06-01",
             "16": "2023-09-11", "17": "2022-06-01", "18": "2025-04-30", "19": "2023-06-01",
             "20": "2026-04-30", "21": "2024-06-01", "22": "2027-04-30", "23": "2025-06-01",
             "24": "2028-04-30"},
}
# Distribution name -> what the code imports, where they differ.
IMPORT_AS = {"pyyaml": ["yaml"], "beautifulsoup4": ["bs4"], "pillow": ["PIL"], "scikit-learn": ["sklearn"],
             "python-dateutil": ["dateutil"], "opencv-python": ["cv2"], "attrs": ["attr", "attrs"],
             "typing-extensions": ["typing_extensions"], "protobuf": ["google.protobuf"],
             "python-dotenv": ["dotenv"], "pyjwt": ["jwt"], "psycopg2-binary": ["psycopg2"],
             "pymysql": ["pymysql"], "msgpack-python": ["msgpack"], "setuptools": ["setuptools", "pkg_resources"],
             "google-cloud-storage": ["google.cloud.storage"], "markupsafe": ["markupsafe"]}
# Used without being imported: the module that needs it, and why.
IMPLICIT = {"tzdata": ("zoneinfo", "zoneinfo reads it where the OS has no time zone data (Windows, slim images)")}
TOOLING = {"pip", "wheel", "setuptools", "pip-tools", "build", "twine"}
UNSUPPORTED = {"go.mod": "Go", "Cargo.toml": "Rust", "Gemfile": "Ruby", "composer.json": "PHP",
               "pom.xml": "Java", "build.gradle": "Java", "Package.swift": "Swift", "mix.exs": "Elixir"}
HIGH = {"known-hole", "eol-runtime", "lock-drift"}


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def vtuple(text):
    nums = re.findall(r"\d+", text.split("+")[0])
    return tuple(int(n) for n in nums[:4]) + (0,) * (4 - min(len(nums), 4))


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.endswith(".egg-info"))
        for f in sorted(files):
            yield os.path.relpath(os.path.join(d, f), root).replace("\\", "/")


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


# ------------------------------------------------------------------ manifests and locks

REQ = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)(\[[^\]]*\])?\s*([^;#]*)")


def parse_requirements(root, rel):
    """name -> {spec, line, comment}; continuation lines and options skipped."""
    out, prev_comment = {}, False
    for i, raw in enumerate(read(root, rel).splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("-") or line.startswith("--"):
            prev_comment = False
            continue
        if line.startswith("#"):
            prev_comment = "via" not in line
            continue
        m = REQ.match(line)
        if m:
            out[norm(m.group(1))] = {"spec": m.group(3).strip().rstrip("\\").strip(), "line": i,
                                     "comment": "#" in raw or prev_comment, "raw": m.group(1)}
        prev_comment = False
    return out


def via_of(root, rel):
    """pip-compile `# via x` comments: name -> who pulls it in."""
    out, cur = {}, None
    for raw in read(root, rel).splitlines():
        m = REQ.match(raw) if raw and not raw[0].isspace() and not raw.startswith("#") else None
        if m:
            cur = norm(m.group(1))
            v = re.search(r"#\s*via\s+(.+)", raw)
            if v:
                out[cur] = v.group(1).strip()
            continue
        v = re.match(r"\s+#\s*(?:via\s+)?(.+)", raw)
        if cur and v:
            out.setdefault(cur, v.group(1).strip())
    return out


def toml(root, rel):
    try:
        import tomllib
    except ImportError:
        return None
    try:
        return tomllib.loads(read(root, rel))
    except ValueError:
        return {}


def pin_of(spec):
    m = re.match(r"^===?\s*([\w.\-+]+)$", spec.strip())
    return m.group(1) if m else None


def allows(spec, version):
    """PEP 440 subset and npm ^ ~ ranges; unknown forms allow."""
    v = vtuple(version)
    for part in filter(None, re.split(r"[,\s]+", spec.strip())):
        m = re.match(r"(===|==|>=|<=|~=|!=|>|<|\^|~|=)?v?([\w.*\-+]+)$", part)
        if not m or m.group(2) in ("*", "latest", "x"):
            continue
        op, want = m.group(1) or "==", m.group(2)
        if want.endswith(".*"):
            n = len(want[:-2].split("."))
            ok = v[:n] == vtuple(want[:-2])[:n]
        else:
            w = vtuple(want)
            if op == "^":
                lead = next((i for i, x in enumerate(w) if x), 2)
                ok = v >= w and v[:lead + 1] == w[:lead + 1]
            elif op in ("~", "~="):
                keep = max(1, len(want.split(".")) - 1) if op == "~=" else 2
                ok = v >= w and v[:keep] == w[:keep]
            else:
                ok = {"==": v == w, "===": v == w, "=": v == w, ">=": v >= w, "<=": v <= w,
                      ">": v > w, "<": v < w, "!=": v != w}[op]
        if not ok:
            return False
    return True


def python_sets(root, files):
    """[(manifest, lock, direct{name: info}, locked{name: version}, via{name: who})]"""
    sets = []
    ins = [f for f in files if re.search(r"(^|/)requirements[^/]*\.in$", f)]
    for f in ins:
        lock = f[:-3] + ".txt"
        locked = {n: pin_of(i["spec"]) for n, i in parse_requirements(root, lock).items()} if lock in files else {}
        sets.append((f, lock if lock in files else None, parse_requirements(root, f), locked, via_of(root, lock)))
    for f in files:
        if re.search(r"(^|/)requirements[^/]*\.txt$", f) and f[:-4] + ".in" not in files:
            direct = parse_requirements(root, f)
            sets.append((f, f, direct, {n: pin_of(i["spec"]) for n, i in direct.items()}, {}))
    for f in files:
        if not f.endswith("pyproject.toml"):
            continue
        data = toml(root, f)
        if data is None:
            continue
        deps = list(data.get("project", {}).get("dependencies", []))
        for extra in data.get("project", {}).get("optional-dependencies", {}).values():
            deps += extra
        direct = {}
        for d in deps:
            m = REQ.match(d)
            if m:
                direct[norm(m.group(1))] = {"spec": m.group(3).strip(), "line": 0, "comment": True, "raw": m.group(1)}
        for name, spec in data.get("tool", {}).get("poetry", {}).get("dependencies", {}).items():
            if name.lower() != "python":
                direct[norm(name)] = {"spec": spec if isinstance(spec, str) else "", "line": 0, "comment": True, "raw": name}
        if not direct:
            continue
        base = os.path.dirname(f)
        lock = next((os.path.join(base, n).replace("\\", "/").lstrip("/") for n in ("poetry.lock", "uv.lock")
                     if os.path.join(base, n).replace("\\", "/").lstrip("/") in files), None)
        locked = {}
        if lock:
            for p in (toml(root, lock) or {}).get("package", []):
                locked[norm(p.get("name", ""))] = p.get("version")
        sets.append((f, lock, direct, locked, {}))
    return sets


def node_sets(root, files):
    sets = []
    for f in files:
        if not f.endswith("package.json") or "node_modules/" in f:
            continue
        try:
            pkg = json.loads(read(root, f))
        except ValueError:
            continue
        direct = {}
        for field in ("dependencies", "devDependencies", "optionalDependencies"):
            for name, spec in (pkg.get(field) or {}).items():
                direct[name] = {"spec": str(spec), "line": 0, "comment": True, "raw": name, "dev": field == "devDependencies"}
        base = os.path.dirname(f)
        lock_rel = os.path.join(base, "package-lock.json").replace("\\", "/").lstrip("/")
        locked, via = {}, {}
        if lock_rel in files:
            try:
                data = json.loads(read(root, lock_rel))
            except ValueError:
                data = {}
            for path, info in (data.get("packages") or {}).items():
                if path.startswith("node_modules/") and "version" in info:
                    locked.setdefault(path.split("node_modules/")[-1], info["version"])
                    for dep in (info.get("dependencies") or {}):
                        via.setdefault(dep, path.split("node_modules/")[-1])
            for name, info in (data.get("dependencies") or {}).items():
                locked.setdefault(name, info.get("version"))
        sets.append((f, lock_rel if lock_rel in files else None, direct, locked, via, pkg))
    return sets


# ------------------------------------------------------------------ holes

def load_advisories(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def holes_from_file(adv, eco, pins):
    found = {}
    for h in adv.get("holes", []):
        if h.get("ecosystem", "").lower() != eco.lower():
            continue
        name = norm(h["name"]) if eco == "PyPI" else h["name"]
        ver = pins.get(name)
        if not ver:
            continue
        v = vtuple(ver)
        if "below" in h and v >= vtuple(h["below"]):
            continue
        if "from" in h and v < vtuple(h["from"]):
            continue
        if "versions" in h and ver not in h["versions"]:
            continue
        found.setdefault(name, []).append(h.get("id", "advisory"))
    return found


def holes_from_osv(eco, pins):
    names = [n for n, v in pins.items() if v]
    if not names:
        return {}
    body = json.dumps({"queries": [{"package": {"name": n, "ecosystem": eco}, "version": pins[n]} for n in names]})
    req = urllib.request.Request(OSV, data=body.encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        results = json.loads(resp.read().decode()).get("results", [])
    return {n: [v["id"] for v in r.get("vulns", [])] for n, r in zip(names, results) if r.get("vulns")}


# ------------------------------------------------------------------ usage

def python_imports(root, files):
    mods = set()
    for f in files:
        if not f.endswith(".py"):
            continue
        try:
            tree = ast.parse(read(root, f))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    mods.add(a.name)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                mods.add(node.module)
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", getattr(node.func, "id", "")) in (
                    "import_module", "__import__") and node.args and isinstance(node.args[0], ast.Constant):
                mods.add(str(node.args[0].value))
    return mods


def node_imports(root, files):
    mods = set()
    pat = re.compile(r"""(?:require\(|import\(|from\s+|import\s+)['"]([^'"./][^'"]*)['"]""")
    for f in files:
        if re.search(r"\.(m?js|cjs|jsx|tsx?|vue|svelte)$", f):
            for m in pat.finditer(read(root, f)):
                spec = m.group(1)
                mods.add("/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0])
    return mods


def named_in(root, files, name, skip):
    """Non-code files that name the package as a word (Dockerfile CMD, Procfile, configs, scripts)."""
    pat = re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(name), re.I)
    hits = []
    for f in files:
        if f in skip or f.endswith((".py", ".lock")) or re.search(r"(^|/)(requirements[^/]*\.(in|txt)|package(-lock)?\.json|pyproject\.toml)$", f):
            continue
        base = os.path.basename(f)
        if base in ("Dockerfile", "Procfile", "Makefile") or base.startswith("Dockerfile") or re.search(
                r"\.(ya?ml|toml|cfg|ini|sh|ps1|json|conf|service)$", f):
            if pat.search(read(root, f)):
                hits.append(f)
    return hits


# ------------------------------------------------------------------ runtimes

def runtimes(root, files):
    found = []
    for f in files:
        base = os.path.basename(f)
        text = read(root, f)
        if base.startswith("Dockerfile"):
            for m in re.finditer(r"(?im)^\s*FROM\s+(?:\S+/)?(python|node):(\d+(?:\.\d+)?)", text):
                found.append((m.group(1), m.group(2), f))
        elif base == ".python-version":
            m = re.match(r"\s*(\d+\.\d+)", text)
            if m:
                found.append(("python", m.group(1), f))
        elif base in (".nvmrc", ".node-version"):
            m = re.match(r"\s*v?(\d+)", text)
            if m:
                found.append(("node", m.group(1), f))
        elif base == "pyproject.toml":
            m = re.search(r"requires-python\s*=\s*['\"][^'\"]*?(?:>=|==|~=)\s*(\d+\.\d+)", text)
            if m:
                found.append(("python", m.group(1), f))
        elif base == "runtime.txt":
            m = re.search(r"python-(\d+\.\d+)", text)
            if m:
                found.append(("python", m.group(1), f))
    return found


# ------------------------------------------------------------------ findings

def scan(root, advisories=None, offline=False, today=None):
    today = today or datetime.date.today()
    files = list(walk(root))
    adv = load_advisories(advisories)
    findings, not_checked, seen = [], [], set()

    def add(kind, name, detail, where):
        fid = f"{kind}:{name}"
        if fid in seen:
            return
        seen.add(fid)
        findings.append({"id": fid, "kind": kind, "severity": "high" if kind in HIGH else "low",
                         "name": name, "detail": detail, "where": where})

    def holes(eco, pins, label):
        try:
            if adv is not None:
                return holes_from_file(adv, eco, pins)
            if offline:
                raise OSError("offline")
            return holes_from_osv(eco, pins)
        except (OSError, ValueError) as e:
            not_checked.append(f"{label}: known holes not checked ({e.__class__.__name__}: {e}); "
                               "pass --advisories FILE or run where OSV.dev is reachable")
            return {}

    py, nd = python_sets(root, files), node_sets(root, files)
    if any(f.endswith("pyproject.toml") for f in files) and toml(root, "pyproject.toml") is None:
        not_checked.append("pyproject.toml: needs Python 3.11+ (tomllib) to read")
    imports = python_imports(root, files) if py else set()
    for manifest, lock, direct, locked, via in py:
        pins = {n: v for n, v in (locked or {}).items() if v}
        unpinned = [n for n in direct if n not in pins]
        for name, ids in sorted(holes("PyPI", pins, f"{lock or manifest} (Python)").items()):
            how = "direct" if name in direct else f"indirect, via {via.get(name, 'another package')}"
            add("known-hole", name, f"{name} {pins[name]} ({how}): {', '.join(ids[:4])}", lock or manifest)
        if unpinned and lock != manifest:
            for n in unpinned:
                add("lock-drift", n, f"{direct[n]['raw']} is in {manifest} but not pinned in "
                    f"{lock or 'any lockfile'}, so installing from the lock leaves it out", lock or manifest)
        elif unpinned:
            not_checked.append(f"{manifest}: {len(unpinned)} unpinned ({', '.join(sorted(unpinned)[:5])}); holes checked only for pins")
        for n, info in direct.items():
            if n in pins and info["spec"] and not allows(info["spec"], pins[n]):
                add("lock-drift", n, f"{lock} pins {n} {pins[n]}, which {manifest} '{info['spec']}' does not allow", lock)
            if lock != manifest and pin_of(info["spec"]) and not info["comment"]:
                add("pinned-no-reason", n, f"{manifest}:{info['line']} pins {info['raw']} exactly with no comment saying why", manifest)
        for n, info in direct.items():
            if n in TOOLING or n.startswith("types-") or n.endswith("-stubs"):
                continue
            mods = IMPORT_AS.get(n, [info["raw"].replace("-", "_"), n.replace("-", "_")])
            if any(m == i or i.startswith(m + ".") for m in mods for i in imports):
                continue
            if n in IMPLICIT and IMPLICIT[n][0] in imports:
                add("used-without-import", n, f"{n}: not imported, but {IMPLICIT[n][1]}; keep it", manifest)
                continue
            where = named_in(root, files, info["raw"], {manifest, lock})
            if where:
                add("used-without-import", n, f"{n}: not imported, but named in {', '.join(where[:3])}; check before removing", manifest)
            else:
                add("unused", n, f"{n} is declared in {manifest} and no Python file imports it", manifest)
    nimports = node_imports(root, files) if nd else set()
    for manifest, lock, direct, locked, via, pkg in nd:
        pins = {n: v for n, v in locked.items() if v}
        label = f"{lock or manifest} (Node)"
        if not lock:
            not_checked.append(f"{manifest}: no package-lock.json, so versions are unknown; holes not checked")
        else:
            for name, ids in sorted(holes("npm", pins, label).items()):
                how = "direct" if name in direct else f"indirect, via {via.get(name, 'another package')}"
                add("known-hole", name, f"{name} {pins[name]} ({how}): {', '.join(ids[:4])}", lock)
            for n, info in direct.items():
                if n not in pins:
                    add("lock-drift", n, f"{n} is in {manifest} but not in {lock}", lock)
                elif not allows(info["spec"], pins[n]):
                    add("lock-drift", n, f"{lock} has {n} {pins[n]}, which {manifest} '{info['spec']}' does not allow", lock)
        scripts = " ".join((pkg.get("scripts") or {}).values())
        for n, info in direct.items():
            if n in nimports or n.startswith("@types/"):
                continue
            short = n.split("/")[-1]
            if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(short), scripts):
                continue
            where = named_in(root, files, short, {manifest, lock})
            if where:
                add("used-without-import", n, f"{n}: not imported, but named in {', '.join(where[:3])}; check before removing", manifest)
            elif not info.get("dev"):
                add("unused", n, f"{n} is in {manifest} dependencies and no source file imports it", manifest)
    for lang, ver, where in runtimes(root, files):
        key = ver if lang == "python" else ver.split(".")[0]
        date = (adv or {}).get("eol", {}).get(lang, {}).get(key) or EOL[lang].get(key)
        if not date:
            not_checked.append(f"{where}: {lang} {ver} end-of-life date unknown")
            continue
        end = datetime.date.fromisoformat(date)
        if end <= today:
            add("eol-runtime", f"{lang}-{key}", f"{where} uses {lang} {ver}, end of life since {date}: no security fixes", where)
        elif (end - today).days <= 180:
            add("eol-soon", f"{lang}-{key}", f"{where} uses {lang} {ver}, end of life on {date}", where)
    for f in files:
        if os.path.basename(f) in UNSUPPORTED:
            not_checked.append(f"{f}: {UNSUPPORTED[os.path.basename(f)]} dependencies are not read by this helper")
    if not py and not nd:
        not_checked.append("no Python or Node manifest found")
    order = {"high": 0, "low": 1}
    findings.sort(key=lambda x: (order[x["severity"]], x["kind"], x["name"]))
    return findings, not_checked


# ------------------------------------------------------------------ state

def load(root, name, default=None):
    try:
        with open(os.path.join(root, STATE, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save(root, name, data):
    os.makedirs(os.path.join(root, STATE), exist_ok=True)
    with open(os.path.join(root, STATE, name), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)


def accepted_now(root, today):
    acc = load(root, "accepted.json", {})
    live = {k: v for k, v in acc.items() if datetime.date.fromisoformat(v["until"]) >= today}
    due = {k: v for k, v in acc.items() if k not in live}
    return live, due


def write_findings(root, findings, not_checked, live, due, extra):
    md = ["# Dependency findings", "", "Worst first. Each high one needs a fix or `--accept ID --reason ... --until ...`.", ""]
    md += extra + ([""] if extra else [])
    for f in findings:
        tag = " (accepted until %s: %s)" % (live[f["id"]]["until"], live[f["id"]]["reason"]) if f["id"] in live else ""
        tag += " (accepted, look again was due %s)" % due[f["id"]]["until"] if f["id"] in due else ""
        md.append(f"- [{f['severity']}] `{f['id']}` {f['detail']}{tag}")
    if not findings:
        md.append("- none in what was checked")
    md += ["", "## Not checked"] + ([f"- {n}" for n in not_checked] or ["- nothing: every manifest found was checked"])
    os.makedirs(os.path.join(root, STATE), exist_ok=True)
    with open(os.path.join(root, STATE, "findings.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    save(root, "last.json", {"ids": [f["id"] for f in findings]})
    return md


def since_last(root, findings, due):
    hist = load(root, "history.json", [])
    lines = []
    if hist:
        last = hist[-1]
        before = set(last.get("left", []))
        new = [f for f in findings if f["id"] not in before]
        lines = [f"Since the check of {last['date']}:"]
        lines += [f"  new: [{f['severity']}] {f['id']} {f['detail']}" for f in new]
    if due:
        lines = lines or ["Since the last check:"]
        lines += [f"  due again: {k} (accepted until {v['until']}: {v['reason']})" for k, v in due.items()]
    if len(lines) == 1:
        lines.append("  nothing new")
    return lines


def manifest_files(root):
    pat = re.compile(r"(^|/)(requirements[^/]*\.(in|txt)|constraints[^/]*\.txt|pyproject\.toml|poetry\.lock|uv\.lock|"
                     r"package\.json|package-lock\.json)$")
    out = {}
    for f in walk(root):
        if pat.search(f):
            out[f] = hashlib.sha256(read(root, f).encode()).hexdigest()
    return out


def pairs(files):
    """(manifest, lock) that must change together."""
    out = []
    for f in files:
        if f.endswith(".in") and f[:-3] + ".txt" in files:
            out.append((f, f[:-3] + ".txt"))
        elif f.endswith("package.json"):
            lock = f[:-len("package.json")] + "package-lock.json"
            if lock in files:
                out.append((f, lock))
        elif f.endswith("pyproject.toml"):
            for n in ("poetry.lock", "uv.lock"):
                lock = f[:-len("pyproject.toml")] + n
                if lock in files:
                    out.append((f, lock))
    return out


def run_tests(root, cmd):
    p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
    out = p.stdout + p.stderr
    counts = [int(g) for m in TESTS_RAN.finditer(out) for g in m.groups() if g]
    return {"cmd": cmd, "exit": p.returncode, "ran": max(counts) if counts else None, "tail": out[-1500:]}


def accept(root, fid, reason, until, today):
    if not reason or not reason.strip():
        print("refused: an acceptance needs --reason saying why it is left as it is")
        return 1
    try:
        end = datetime.date.fromisoformat(until or "")
    except ValueError:
        print("refused: --until must be a date, YYYY-MM-DD, when this is looked at again")
        return 1
    if end <= today:
        print(f"refused: --until {until} is not in the future")
        return 1
    ids = (load(root, "last.json") or {}).get("ids", [])
    if fid not in ids:
        print(f"refused: {fid} is not a current finding (run the scan first; ids are in .deps/findings.md)")
        return 1
    acc = load(root, "accepted.json", {})
    acc[fid] = {"reason": reason.strip(), "until": until, "date": today.isoformat()}
    save(root, "accepted.json", acc)
    print(f"accepted {fid} until {until}")
    return 0


def done(root, cmd, advisories, offline, today):
    base = load(root, "baseline.json")
    if not base:
        print("DEPS: not done - no baseline. Run `--run CMD` before changing anything.")
        return 1
    cmd = cmd or base["suite"]["cmd"]
    advisories = advisories or base.get("advisories")
    offline = offline or base.get("offline", False)
    findings, not_checked = scan(root, advisories, offline, today)
    live, due = accepted_now(root, today)
    problems = []
    for f in findings:
        if f["severity"] == "high" and f["id"] not in live:
            problems.append(f"undecided [{f['kind']}] {f['detail']}: fix it, or "
                            f"`--accept {f['id']} --reason ... --until YYYY-MM-DD`")
    now = run_tests(root, cmd)
    was = base["suite"]
    if was["exit"] == 0 and now["exit"] != 0:
        problems.append(f"the tests passed before and fail now ({cmd}):\n{now['tail'][-800:]}")
    if was["ran"] and (now["ran"] or 0) < was["ran"]:
        problems.append(f"{now['ran'] or 0} tests ran, {was['ran']} before")
    cur = manifest_files(root)
    for manifest, lock in pairs(set(cur) | set(base["files"])):
        m_changed = cur.get(manifest) != base["files"].get(manifest)
        l_changed = cur.get(lock) != base["files"].get(lock)
        if m_changed and not l_changed and lock in cur:
            problems.append(f"{manifest} changed but {lock} did not: regenerate the lock")
    write_findings(root, findings, not_checked, live, due, [])
    if problems:
        print("DEPS: not done")
        for p in problems:
            print("  - " + p)
        return 1
    hist = load(root, "history.json", [])
    hist.append({"date": today.isoformat(), "left": [f["id"] for f in findings],
                 "accepted": sorted(live), "not_checked": not_checked,
                 "tests": {"before": was["ran"], "after": now["ran"]}})
    save(root, "history.json", hist)
    os.remove(os.path.join(root, STATE, "baseline.json"))
    highs = sum(1 for f in findings if f["severity"] == "high")
    print(f"{highs} high findings left, all accepted; {len(findings) - highs} low; "
          f"tests {was['ran']} before, {now['ran']} after; {len(not_checked)} not checked (.deps/findings.md)")
    print("DEPS: done")
    return 0


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--run", help="test command, e.g. \"python -m unittest discover tests\"")
    ap.add_argument("--done", action="store_true")
    ap.add_argument("--accept", metavar="ID")
    ap.add_argument("--reason")
    ap.add_argument("--until", metavar="YYYY-MM-DD")
    ap.add_argument("--advisories", metavar="FILE", help="known holes and end-of-life dates as JSON, instead of OSV.dev")
    ap.add_argument("--offline", action="store_true", help="do not ask OSV.dev")
    ap.add_argument("--today", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    root = os.path.abspath(a.repo)
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    advisories = os.path.abspath(a.advisories) if a.advisories else None
    if a.accept:
        return accept(root, a.accept, a.reason, a.until, today)
    if a.done:
        return done(root, a.run, advisories, a.offline, today)
    findings, not_checked = scan(root, advisories, a.offline, today)
    live, due = accepted_now(root, today)
    md = write_findings(root, findings, not_checked, live, due, since_last(root, findings, due))
    print("\n".join(md[4:]))
    if a.run:
        suite = run_tests(root, a.run)
        if not suite["ran"]:
            print(f"refused: `{a.run}` ran no tests I could count, so nothing was recorded.\n{suite['tail'][-500:]}")
            return 1
        save(root, "baseline.json", {"files": manifest_files(root), "suite": suite,
                                     "advisories": advisories, "offline": a.offline})
        print(f"recorded: {suite['ran']} tests, exit {suite['exit']}. Fix or accept, then `--done`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
