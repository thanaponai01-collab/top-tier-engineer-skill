#!/usr/bin/env python3
"""checkup.py — one report on how well a codebase is structured, ranked by where changes land.

Runs the sibling helpers that are installed (structure-gate's structure-report.py, latent-audit's
graph-audit.py, arch-design's change-map.py and dep-map.py, feature-map's features.py) over the
repo's git-tracked files and folds what they find into eight sections:

  find       easy to find things          (FEATURES.md, checked by features.py)
  locality   one change in one place      (files that change together, and whether an import links them)
  direction  dependencies point one way   (import cycles, declared layers)
  depth      deep modules, narrow doors   (tangled functions, long files, pass-through modules, one-implementer seams)
  oneway     one way per job              (copied blocks, two libraries doing one job)
  io         logic apart from I/O         (modules that both do I/O and hold tangled decisions)
  dead       no dead code                 (modules nothing imports or names, unused functions)
  tests      tests that can fail          (never measured here: verify-loop runs that)

Every finding is weighted by the history: commits plus twice the fix commits of its files in the
last 300 commits (for a pair, the commits that touched both). A finding whose files no commit in
the last 100 touched is `idle`. A section nothing measured says `not checked: <why>`.

Usage:
  checkup.py [repo]            the report
  checkup.py [repo] --json     the same, as JSON
  checkup.py [repo] --gate     the four stages; drafts slots in .checkup/notes.md
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _encoding import utf8_streams  # noqa: E402

SKILLS = os.path.dirname(os.path.dirname(HERE))
STATE = ".checkup"
REPORT = f"{STATE}/report.json"
NOTES = f"{STATE}/notes.md"
FIX = re.compile(r"\b(fix|fixes|fixed|bug|regression|hotfix|revert)\b", re.I)
WINDOW, RECENT, BULK, TOP, DEEPEST, READ = 300, 100, 50, 3, 12, 8
MIN_SHARED, MAX_PAIRS = 3, 20
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb", ".php",
            ".cs", ".c", ".h", ".cpp", ".hpp", ".swift", ".scala", ".sh"}
SECTIONS = [
    ("find", "Easy to find things", "feature-map"),
    ("locality", "One change in one place", "untangle"),
    ("direction", "Dependencies point one way", "arch-design"),
    ("depth", "Deep modules, narrow doors", "arch-design"),
    ("oneway", "One way per job", "cleanup"),
    ("io", "Logic apart from I/O", "arch-design"),
    ("dead", "No dead code", "latent-audit"),
    ("tests", "Tests that can fail", "verify-loop"),
]
TITLE = {k: t for k, t, _ in SECTIONS}
FIXER = {k: f for k, _, f in SECTIONS}
PY_ONLY = {"direction", "io", "dead"}
JOBS = {
    "http": ["urllib.request", "http.client", "requests", "httpx", "aiohttp", "urllib3"],
    "database": ["sqlite3", "psycopg2", "psycopg", "sqlalchemy", "pymongo", "redis", "pymysql",
                 "asyncpg", "aiosqlite", "peewee"],
    "mail": ["smtplib", "yagmail", "sendgrid"],
}
EXTRA_IO = sorted({lib for libs in JOBS.values() for lib in libs})
VERDICTS = ("good", "in places", "poor", "not checked")


# ---------------- plumbing ----------------------------------------------------------------------
def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, p.stdout


def sibling(skill, name):
    p = os.path.join(SKILLS, skill, "scripts", name)
    return p if os.path.isfile(p) else None


def installed(skill):
    return os.path.isfile(os.path.join(SKILLS, skill, "SKILL.md"))


def run_helper(script, args, cwd, timeout=900):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        p = subprocess.run([sys.executable, script, *args], cwd=cwd, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return None, "", f"timed out after {timeout}s"
    return p.returncode, p.stdout, p.stderr


def first_json(text):
    i = text.find("{")
    if i < 0:
        return None
    try:
        return json.JSONDecoder().raw_decode(text[i:])[0]
    except ValueError:
        return None


def tracked_files(repo):
    rc, out = git(repo, "ls-files", "-z")
    return {p for p in out.split("\0") if p} if rc == 0 else set()


def tree_hash(repo):
    h = hashlib.sha256()
    for args in (("rev-parse", "HEAD"), ("ls-files", "-s", "--", ".", f":(exclude){STATE}"),
                 ("diff", "HEAD", "--", ".", f":(exclude){STATE}")):
        h.update(git(repo, *args)[1].encode("utf-8", "replace"))
    return h.hexdigest()[:16]


def cache_key(repo):
    """The tracked tree and the history settings: a report is reused only while both are the same."""
    return f"{tree_hash(repo)}-w{WINDOW}-r{RECENT}-v2"


# ---------------- history -----------------------------------------------------------------------
def set_history(window, recent):
    global WINDOW, RECENT
    WINDOW, RECENT = window, recent


def read_history(repo):
    rc, out = git(repo, "log", "-n", str(WINDOW), "--no-merges", "--name-only", "--format=@@%H\t%s")
    commits = []
    if rc != 0:
        return commits
    for block in out.split("@@")[1:]:
        lines = block.strip("\n").splitlines()
        sha, _, subject = lines[0].partition("\t")
        files = [ln.strip() for ln in lines[1:] if ln.strip()]
        commits.append({"sha": sha, "subject": subject, "files": files, "fix": bool(FIX.search(subject))})
    return commits


class History:
    def __init__(self, commits):
        self.commits = [c for c in commits if len(c["files"]) <= BULK]
        self.n = len(commits)
        self.recent = {f for c in commits[:RECENT] for f in c["files"]}

    def touching(self, files, joint):
        fs = set(files)
        if joint:
            return [c for c in self.commits if fs <= set(c["files"])]
        return [c for c in self.commits if fs & set(c["files"])]

    def weigh(self, files, joint):
        if joint:
            hits = self.touching(files, True)
            return len(hits), sum(c["fix"] for c in hits), hits
        best = (0, 0, [])
        for f in files:
            hits = self.touching([f], False)
            c, x = len(hits), sum(h["fix"] for h in hits)
            if c + 2 * x > best[0] + 2 * best[1]:
                best = (c, x, hits)
        return best


# ---------------- probes ------------------------------------------------------------------------
def probe_structure(repo):
    s = sibling("structure-gate", "structure-report.py")
    if not s:
        return {"status": "missing", "why": "structure-gate is not installed"}
    rc, out, err = run_helper(s, ["--json", repo], repo)
    r = first_json(out)
    if r is None:
        return {"status": "failed", "why": (err or out).strip()[-300:] or f"exit {rc}"}
    return {"status": "ok", "data": r}


def probe_graph(repo, raw):
    s = sibling("latent-audit", "graph-audit.py")
    if not s:
        return {"status": "missing", "why": "latent-audit is not installed"}
    edges = os.path.join(raw, "edges.json")
    args = [repo, "--json", "--edges", edges]
    layers = os.path.join(repo, "layers.txt")
    if os.path.isfile(layers):
        args += ["--layers", layers]
    rc, out, err = run_helper(s, args, repo)
    if "blocked(no analyzable source)" in out:
        return {"status": "none", "why": "no Python modules"}
    r = first_json(out)
    if r is None or not os.path.isfile(edges):
        return {"status": "failed", "why": (err or out).strip()[-300:] or f"exit {rc}"}
    with open(edges, encoding="utf-8") as fh:
        g = json.load(fh)
    r["modules_map"] = g["modules"]
    r["file_edges"] = sorted({tuple(sorted((g["modules"][e["from"]], g["modules"][e["to"]])))
                              for e in g["edges"] if e["from"] in g["modules"] and e["to"] in g["modules"]})
    r["edges_file"] = edges
    return {"status": "ok", "data": r}


def is_test(path):
    name = os.path.basename(path)
    return (name.startswith("test_") or name.endswith(("_test.py", ".test.js", ".test.ts", ".spec.js", ".spec.ts"))
            or "/tests/" in "/" + path or "/test/" in "/" + path)


def pairs_from_history(hist, tracked):
    """Files that changed together in MIN_SHARED+ commits. A test and the code it tests change
    together by design, so a pair with a test file in it is left out."""
    count = {}
    for c in hist.commits:
        files = sorted(f for f in set(c["files"]) if f in tracked and not is_test(f)
                       and not f.startswith(STATE + "/"))
        for i, a in enumerate(files):
            for b in files[i + 1:]:
                count[(a, b)] = count.get((a, b), 0) + 1
    rows = [(a, b, n) for (a, b), n in count.items() if n >= MIN_SHARED]
    return sorted(rows, key=lambda r: (-r[2], r[0], r[1]))[:MAX_PAIRS]


def probe_dep(repo, graph):
    s = sibling("arch-design", "dep-map.py")
    if not s:
        return {"status": "missing", "why": "arch-design is not installed"}
    if graph["status"] != "ok":
        return {"status": "none", "why": "no import graph: " + graph.get("why", "")}
    args = [graph["data"]["edges_file"], "--json"]
    for lib in EXTRA_IO:
        args += ["--io", lib]
    rc, out, err = run_helper(s, args, repo)
    r = first_json(out)
    if r is None:
        return {"status": "failed", "why": (err or out).strip()[-300:] or f"exit {rc}"}
    return {"status": "ok", "data": r}


def probe_features(repo):
    if not os.path.isfile(os.path.join(repo, "FEATURES.md")):
        return {"status": "none", "why": "no FEATURES.md: nothing maps each feature to its way in "
                                         "(feature-map writes one)"}
    s = sibling("feature-map", "features.py")
    if not s:
        return {"status": "missing", "why": "feature-map is not installed"}
    rc, out, err = run_helper(s, ["check", repo], repo)
    if rc is None:
        return {"status": "failed", "why": err}
    return {"status": "ok", "data": {"holds": rc == 0, "tail": (out + err).strip().splitlines()[-5:]}}


# ---------------- report ------------------------------------------------------------------------
class Builder:
    def __init__(self, repo, tracked, hist):
        self.repo, self.tracked, self.hist = repo, tracked, hist
        self.findings, self.dropped = [], 0

    def rel(self, p):
        if not os.path.isabs(p):
            p = os.path.join(self.repo, p)
        return os.path.relpath(os.path.abspath(p), self.repo).replace("\\", "/")

    def add(self, section, kind, files, where, detail, joint=False, value=0):
        files = sorted({self.rel(f) for f in files})
        if not files or any(f not in self.tracked or f.startswith(STATE + "/") for f in files):
            self.dropped += 1
            return
        where = re.sub(r"\s+", "_", where)
        commits, fixes, hits = self.hist.weigh(files, joint)
        self.findings.append({
            "id": f"{section}/{kind}@{where}", "section": section, "kind": kind, "files": files,
            "where": where, "detail": detail, "joint": joint, "commits": commits, "fixes": fixes,
            "weight": commits + 2 * fixes, "idle": not (set(files) & self.hist.recent),
            "shas": [h["sha"][:8] for h in hits[:5]], "value": value})


def module_files(graph):
    return graph["data"]["modules_map"] if graph["status"] == "ok" else {}


def build(repo):
    repo = os.path.abspath(repo)
    tracked = tracked_files(repo)
    hist = History(read_history(repo))
    raw = tempfile.mkdtemp(prefix="checkup-")
    try:
        probes = {"structure": probe_structure(repo), "graph": probe_graph(repo, raw),
                  "features": probe_features(repo)}
        probes["dep"] = probe_dep(repo, probes["graph"])
    finally:
        shutil.rmtree(raw, ignore_errors=True)
    b = Builder(repo, tracked, hist)
    sections = {k: {"measured": False, "why": "", "notes": []} for k, _, _ in SECTIONS}

    def measured(key, note=None):
        sections[key]["measured"] = True
        if note:
            sections[key]["notes"].append(note)

    def unmeasured(key, why):
        if not sections[key]["measured"] and not sections[key]["why"]:
            sections[key]["why"] = why

    st, gr, dp, fe = (probes[k] for k in ("structure", "graph", "dep", "features"))
    mods = module_files(gr)

    # find
    if fe["status"] == "ok":
        measured("find")
        if not fe["data"]["holds"]:
            b.add("find", "map-drift", ["FEATURES.md"], "FEATURES.md",
                  "FEATURES.md no longer matches the code: " + " / ".join(fe["data"]["tail"]))
    else:
        unmeasured("find", fe["why"])

    # locality
    if hist.n:
        measured("locality", f"pairs from {hist.n} commits ({len(hist.commits)} under {BULK} files); "
                             "a test and its code are left out")
        linked = {frozenset(b.rel(p) for p in e) for e in gr["data"]["file_edges"]} if gr["status"] == "ok" else None
        for a, c2, shared in pairs_from_history(hist, tracked):
            tail = ""
            if linked is not None and a.endswith(".py") and c2.endswith(".py"):
                tail = (", and one imports the other" if frozenset((a, c2)) in linked
                        else ", with no import between them")
            b.add("locality", "pair", [a, c2], f"{a}+{c2}", f"changed together in {shared} commits{tail}",
                  joint=True, value=shared)
    else:
        unmeasured("locality", "no commits to read")

    # direction
    if dp["status"] == "ok":
        measured("direction")
        for cyc in dp["data"].get("cycles", []):
            files = [mods[m] for m in cyc["modules"] if m in mods]
            b.add("direction", "cycle", files, "+".join(sorted(m.split(".")[-1] for m in cyc["modules"])),
                  "import cycle: " + " <-> ".join(cyc["modules"]))
    elif st["status"] == "ok" and st["data"]["by_kind"].get("import_cycle") is not None:
        measured("direction")
        for f in st["data"]["findings"]:
            if f["kind"] == "import_cycle":
                files = [p for p in tracked if p.endswith(".py") and
                         os.path.splitext(os.path.basename(p))[0] in f["detail"].split(": ")[-1].split(" -> ")]
                b.add("direction", "cycle", files, f["symbol"], f["detail"])
    else:
        unmeasured("direction", dp.get("why") or "no import graph")
    if gr["status"] == "ok":
        if gr["data"].get("layers_declared"):
            for x in gr["data"].get("layer_breaches", []):
                b.add("direction", "layer", [x["file"]], f"{b.rel(x['file'])}:{x['line']}",
                      f"{x['edge']}: {x['rule']}")
        elif sections["direction"]["measured"]:
            sections["direction"]["notes"].append(
                "layers not checked: no layers.txt at the root says which layer may import which")

    # depth (and the tangled functions the io section reads)
    tangled = {}
    if st["status"] == "ok":
        cov = st["data"].get("coverage", {})
        measured("depth", f"{cov.get('pct_entered', 0)}% of {cov.get('code_lines', 0)} code lines entered by a "
                          "parser (deep on Python, length and copies only elsewhere)")
        merged = {}
        for f in st["data"]["findings"]:
            if f["kind"] in ("cyclomatic", "nesting_depth", "function_lines"):
                key = (b.rel(f["file"]), f["symbol"])
                m = merged.setdefault(key, {"line": f["line"], "details": [], "value": 0})
                m["details"].append(f["detail"])
                if f["kind"] == "cyclomatic":
                    m["value"] = f["value"]
            elif f["kind"] == "file_lines":
                b.add("depth", "long-file", [f["file"]], b.rel(f["file"]), f["detail"].replace("�", "-"),
                      value=f["value"] // 10)
        for (path, sym), m in sorted(merged.items()):
            tangled.setdefault(path, []).append(sym)
            b.add("depth", "tangled", [path], f"{path}:{m['line']}", f"{sym}(): " + "; ".join(
                d.split(") ", 1)[-1] for d in m["details"]), value=m["value"])
    else:
        unmeasured("depth", st["why"])
    if dp["status"] == "ok":
        measured("depth")
        for p in dp["data"].get("pass_through", []):
            if p["module"] in mods:
                b.add("depth", "pass-through", [mods[p["module"]]], p["module"],
                      f"every function only forwards its arguments; imported by {p['imported_by']} module(s)")
        for s in dp["data"].get("seams", []):
            if s["verdict"] == "hypothetical" and s["module"] in mods:
                b.add("depth", "one-implementer", [mods[s["module"]]], f"{s['module']}.{s['seam']}",
                      f"interface {s['seam']} has {len(s['implementers'])} implementer(s)")
        for h in dp["data"].get("hubs", []):
            if h["risky"] and h["module"] in mods:
                b.add("depth", "risky-hub", [mods[h["module"]]], h["module"],
                      f"imported by {h['fan_in']} modules and imports {h['fan_out']}: a change here ripples")

    # oneway
    if st["status"] == "ok":
        measured("oneway")
        last_copy = {}
        for f in sorted(st["data"]["findings"], key=lambda x: (x["file"], x["line"])):
            if f["kind"] == "duplication":
                # One copied block is reported once per starting line; keep the first of a run.
                key = (b.rel(f["file"]), f["value"])
                if f["line"] - last_copy.get(key, -99) <= 6:
                    last_copy[key] = f["line"]
                    continue
                last_copy[key] = f["line"]
                b.add("oneway", "copy", [f["file"]], f"{b.rel(f['file'])}:{f['line']}", f["detail"],
                      value=f["value"])
    if dp["status"] == "ok":
        measured("oneway")
        for job, libs in JOBS.items():
            users = {}
            for row in dp["data"].get("io", []):
                for lib in row["libs"]:
                    root = next((x for x in libs if lib == x or lib.startswith(x + ".")), None)
                    if root and row["module"] in mods:
                        users.setdefault(root, set()).add(row["module"])
            if len(users) >= 2:
                files = [mods[m] for ms in users.values() for m in ms]
                b.add("oneway", "two-ways", files, job, f"{job} is done with {len(users)} libraries: " + "; ".join(
                    f"{lib} in {', '.join(sorted(ms))}" for lib, ms in sorted(users.items())))
    if not sections["oneway"]["measured"]:
        unmeasured("oneway", st.get("why") or dp.get("why", ""))

    # io
    if dp["status"] == "ok":
        rows = [r for r in dp["data"].get("io", []) if r["module"] in mods]
        measured("io", f"{len(rows)} module(s) do network, database or process I/O"
                 + (": " + ", ".join(r["module"] for r in rows[:6]) if rows else ""))
        if st["status"] != "ok":
            sections["io"]["notes"].append("tangled functions not measured, so decisions mixed with I/O are not found")
        for r in rows:
            path = b.rel(mods[r["module"]])
            if path in tangled:
                b.add("io", "decisions-with-io", [path], path,
                      f"imports {', '.join(r['libs'])} and holds tangled decisions in "
                      f"{', '.join(s + '()' for s in tangled[path])}: they cannot run without that I/O")
    else:
        unmeasured("io", dp.get("why") or "no import graph")

    # dead
    if gr["status"] == "ok":
        measured("dead", "suspected: nothing in the repo imports or names these; latent-audit proves it by running")
        for d in gr["data"].get("dead_modules", []):
            b.add("dead", "dead-module", [d["file"]], b.rel(d["file"]), f"module {d['module']}: nothing imports or names it")
        for u in gr["data"].get("unused_defs", []):
            b.add("dead", "unused-def", [u["file"]], f"{b.rel(u['file'])}:{u['line']}", f"{u['name']}() is never called")
    else:
        unmeasured("dead", gr["why"])

    # tests
    unmeasured("tests", "checking it means running the tests against broken code; verify-loop does that")

    for k in sections:
        if not sections[k]["measured"] and not sections[k]["why"]:
            sections[k]["why"] = "no helper measured it"
    # Same weight (same file's history): the worse shape first.
    findings = sorted(b.findings, key=lambda f: (-f["weight"], -f["value"], f["id"]))
    code = [p for p in tracked if os.path.splitext(p)[1].lower() in CODE_EXT]
    opaque = []
    # The files changes land in most: stage 3 has the agent read each one for what no section
    # measures (a wrong total, a retry that charges twice), so the report does not narrow the look.
    due = []
    for p in code:
        if is_test(p) or p.startswith(STATE + "/") or len(source_lines(repo, p)) < 3:
            continue
        c, x, _ = hist.weigh([p], False)
        if c:
            due.append((c + 2 * x, p))
    read_due = [p for _, p in sorted(due, key=lambda t: (-t[0], t[1]))[:READ]]
    if st["status"] == "ok":
        opaque = [f"{b.rel(f['file'])}:{f['line']}" for f in st["data"]["findings"] if f["kind"] == "opaque_code"]
    return {
        "hash": cache_key(repo), "tracked": len(tracked), "code_files": len(code),
        "history": {"commits": hist.n, "window": WINDOW, "recent": RECENT},
        "probes": {k: {"status": v["status"], "why": v.get("why", "")} for k, v in probes.items()},
        "opaque": opaque, "dropped": b.dropped, "sections": sections, "findings": findings,
        "read_due": read_due,
    }


def source_lines(repo, rel):
    try:
        with open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as fh:
            return [ln for ln in fh.read().splitlines() if ln.strip()]
    except OSError:
        return []


def load_or_build(repo, fresh=False):
    path = os.path.join(repo, REPORT)
    if not fresh and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as fh:
                r = json.load(fh)
            if r.get("hash") == cache_key(repo):
                return r
        except (OSError, ValueError):
            pass
    r = build(repo)
    os.makedirs(os.path.join(repo, STATE), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(r, fh, indent=1)
    return r


def measured_line(r):
    probes = ", ".join(f"{k} {v['status']}" + (f" ({v['why']})" if v["status"] not in ("ok",) and v["why"] else "")
                       for k, v in r["probes"].items())
    s = (f"Measured: {r['tracked']} tracked files, {r['code_files']} of them code; "
         f"{r['history']['commits']} commits of history. Helpers: {probes}.")
    if r["opaque"]:
        s += f" No parser entered {len(r['opaque'])} region(s): {', '.join(r['opaque'][:5])}."
    if r["dropped"]:
        s += f" {r['dropped']} finding(s) in untracked or ignored paths dropped."
    return s


def describe(f):
    hist = "idle: no commit in the last 100 touched it" if f["idle"] else \
        f"{f['commits']} commit(s), {f['fixes']} fix(es){' together' if f['joint'] else ''}"
    return f"weight {f['weight']:>3}  {f['id']}\n        {f['detail']} [{hist}]"


def print_report(r):
    print(measured_line(r))
    print(f"Weight = commits + 2 x fix commits in the last {WINDOW}; a pair counts only commits that touched both.")
    print()
    print("TOP (highest weight first)")
    for f in r["findings"][:TOP] or []:
        print("  " + describe(f))
    if not r["findings"]:
        print("  no findings in what was measured")
    for key, title, fixer in SECTIONS:
        sec = r["sections"][key]
        mine = [f for f in r["findings"] if f["section"] == key]
        print()
        scope = " (Python only)" if key in PY_ONLY else ""
        if not sec["measured"]:
            print(f"## {title}{scope}: not checked: {sec['why']}")
            continue
        print(f"## {title}{scope}: {len(mine)} finding(s)" + (f"; fix with {fixer}" if mine and installed(fixer) else ""))
        for n in sec["notes"]:
            print(f"  note: {n}")
        for f in mine[:10]:
            print("  " + describe(f))
        if len(mine) > 10:
            print(f"  ... {len(mine) - 10} more in {REPORT}")
    print()
    print("## Read these: where changes land most, for what no section measures")
    for p in r.get("read_due", []):
        print(f"  {p}")


# ---------------- gate --------------------------------------------------------------------------
NOTES_HEAD = """# Checkup notes

## account
<!-- One line per finding you account for: `- <id>: cost: <commits that show what it costs>` or
`- <id>: none: <why the shape is right>`. A cost cites at least one commit that touched the
finding's files; an idle finding's cost is `cost: next: <the coming change it will slow down>`.
Add a line for any other finding you want in the top three. -->

## read
<!-- One line per file the report says to read, after reading it whole, for what no section
measures (a wrong result, a retry that can repeat a payment, a missing check):
`- <path>: risk: <name>(): <what can go wrong>` or `- <path>: nothing: <name>(): <what it does>`.
<name> is a function or class in that file. Add a line for any other file you read. -->

## answer
"""
SLOT = "[[fill"
LINE = re.compile(r"^- (\S+): (.*)$")
SHA = re.compile(r"\b[0-9a-f]{7,40}\b")


def read_notes(repo):
    path = os.path.join(repo, NOTES)
    if not os.path.isfile(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(NOTES_HEAD)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def split_notes(text):
    parts, cur = {"account": [], "read": [], "answer": []}, None
    for ln in text.splitlines():
        h = ln.strip().lower()
        if h.startswith("## "):
            cur = h[3:].strip() if h[3:].strip() in parts else None
            continue
        m = LINE.match(ln.strip())
        if cur and m:
            parts[cur].append((m.group(1), m.group(2).strip()))
    return {k: filled_first(v) for k, v in parts.items()}


def filled_first(pairs):
    """A key written twice (the agent's line and a drafted slot) keeps the filled line, so a
    slot drafted before the agent's own line never hides it."""
    out = {}
    for k, v in pairs:
        if k not in out or SLOT in out[k]:
            out[k] = v
    return list(out.items())


def append_slots(repo, section, lines):
    if not lines:
        return
    path = os.path.join(repo, NOTES)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    head = f"## {section}"
    out, done = [], False
    rows = text.splitlines()
    i = 0
    while i < len(rows):
        out.append(rows[i])
        if rows[i].strip().lower() == head and not done:
            j = i + 1
            while j < len(rows) and not rows[j].strip().startswith("## "):
                out.append(rows[j])
                j += 1
            while out and not out[-1].strip():
                out.pop()
            out += lines + [""]
            done = True
            i = j
            continue
        i += 1
    if not done:
        out += ["", head] + lines
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out).rstrip("\n") + "\n")


def commit_touches(repo, sha, files):
    rc, out = git(repo, "show", "--name-only", "--format=", sha)
    return rc == 0 and bool(set(out.split()) & set(files))


def check_account(repo, r, notes):
    by_id = {f["id"]: f for f in r["findings"]}
    have = dict(notes["account"])
    # Walk down by weight until TOP findings are not `none:`, so a shape that is right
    # hands its slot to the next finding; stop after DEEPEST so the list stays short.
    want, kept = [], 0
    for f in r["findings"][:DEEPEST]:
        if kept >= TOP:
            break
        if have.get(f["id"], "").startswith("none:"):
            continue
        kept += 1
        if f["id"] not in have:
            want.append(f["id"])
    append_slots(repo, "account", [f"- {i}: {SLOT}: cost: <commits> | none: <why>]]" for i in want])
    for i in want:
        have[i] = SLOT
    problems, costs = [], {}
    for i, text in have.items():
        f = by_id.get(i)
        if f is None:
            problems.append(f"- {i}: the report holds no such finding now (the code changed?); drop the line")
            continue
        if SLOT in text:
            problems.append(f"- {i}: fill the slot: `cost: <commits>` or `none: <why>`")
        elif text.startswith("none:"):
            if len(text[5:].split()) < 3:
                problems.append(f"- {i}: `none:` needs the reason the shape is right")
        elif text.startswith("cost:"):
            body = text[5:].strip()
            if f["idle"] and body.startswith("next:"):
                if len(body[5:].split()) < 3:
                    problems.append(f"- {i}: `cost: next:` needs the coming change it will slow down")
                else:
                    costs[i] = body
                continue
            shas = SHA.findall(body)
            if not any(commit_touches(repo, s, f["files"]) for s in shas):
                hint = (f" (it is idle: cite an older commit, or `cost: next: <the coming change>`)"
                        if f["idle"] else f" (these touched them: {', '.join(f['shas'])})")
                problems.append(f"- {i}: a cost cites a commit that touched {', '.join(f['files'])}{hint}")
            else:
                costs[i] = body
        else:
            problems.append(f"- {i}: start with `cost:` or `none:`")
    return problems, costs


READ_LINE = re.compile(r"^(risk|nothing):\s*([A-Za-z_][\w.]*)\(\):\s*(.*)$")


def check_read(repo, r, notes):
    """Each file due gets a line naming a function in it and what reading it found."""
    have = dict(notes["read"])
    want = [p for p in r.get("read_due", []) if p not in have]
    append_slots(repo, "read", [f"- {p}: {SLOT}: risk: <name>(): <what can go wrong> | "
                                f"nothing: <name>(): <what it does>]]" for p in want])
    for p in want:
        have[p] = SLOT
    tracked = tracked_files(repo)
    problems, risks = [], []
    for p, text in have.items():
        if p not in tracked:
            problems.append(f"- {p}: not a tracked file; name a file by its path from the repo root")
            continue
        if SLOT in text:
            problems.append(f"- {p}: read the file, then `risk: <name>(): <what>` or `nothing: <name>(): <what it does>`")
            continue
        m = READ_LINE.match(text)
        if not m:
            problems.append(f"- {p}: start with `risk: <name>():` or `nothing: <name>():`")
            continue
        kind, name, what = m.groups()
        src = "\n".join(source_lines(repo, p))
        if not re.search(rf"\b{re.escape(name.split('.')[-1])}\b", src):
            problems.append(f"- {p}: {name}() is not in that file; name a function or class it holds")
        elif len(what.split()) < (4 if kind == "risk" else 3):
            problems.append(f"- {p}: say what {name}() " + ("can get wrong" if kind == "risk" else "does"))
        elif kind == "risk":
            risks.append((p, name, what))
    return problems, risks


def read_fixes(text):
    """`- fix <n>: <id>` lines under `## answer`."""
    answer = text.lower().split("## answer", 1)
    if len(answer) < 2:
        return {}
    body = text[len(answer[0]) + len("## answer"):]
    return {int(k): v for k, v in filled_first(
        (m.group(1), m.group(2).strip()) for m in re.finditer(r"^- fix (\d+): (.*)$", body, re.M))}


def check_answer(repo, r, notes, costs):
    by_id = {f["id"]: f for f in r["findings"]}
    ranked = sorted((by_id[i] for i in costs), key=lambda f: (-f["weight"], f["id"]))[:TOP]
    have = dict(notes["answer"])
    fixes = read_fixes(read_notes(repo))
    slots = [f"- {k}: {SLOT}: good | in places | poor | not checked]]" for k, _, _ in SECTIONS if k not in have]
    slots += [f"- fix {n}: {SLOT}: a finding id]]" for n in range(1, len(ranked) + 1) if n not in fixes]
    append_slots(repo, "answer", slots)
    text = read_notes(repo)
    have, fixes = dict(split_notes(text)["answer"]), read_fixes(text)
    problems = []
    for key, title, _ in SECTIONS:
        v = have.get(key, SLOT)
        sec = r["sections"][key]
        mine = [f for f in r["findings"] if f["section"] == key]
        with_cost = [f for f in mine if f["id"] in costs]
        if SLOT in v:
            problems.append(f"- {key}: fill: good | in places | poor | not checked")
        elif v not in VERDICTS:
            problems.append(f"- {key}: `{v}` is not one of good | in places | poor | not checked")
        elif not sec["measured"] and v != "not checked":
            problems.append(f"- {key}: nothing measured it ({sec['why']}), so it is `not checked`")
        elif sec["measured"] and v == "not checked":
            problems.append(f"- {key}: it was measured; say what the measurement allows")
        elif v == "good" and with_cost:
            problems.append(f"- {key}: not `good` while {with_cost[0]['id']} has a cost")
        elif v == "poor" and not with_cost:
            problems.append(f"- {key}: `poor` needs a finding in it with a cost")
        elif v == "in places" and not mine:
            problems.append(f"- {key}: `in places` needs a finding in it")
    for n, f in enumerate(ranked, 1):
        got = fixes.get(n, SLOT)
        if got != f["id"]:
            problems.append(f"- fix {n}: should be {f['id']} (weight {f['weight']}): the fixes are the "
                            "findings with a cost, highest weight first")
    for n in fixes:
        if n > len(ranked):
            problems.append(f"- fix {n}: only {len(ranked)} finding(s) have a cost; drop it")
    return problems, have, ranked


def gate(repo):
    r = load_or_build(repo)
    print(measured_line(r))
    if r["code_files"] == 0:
        print("1. Measure: OPEN. No tracked code file: commit the code, then rerun.")
        print("CHECKUP-GATE: open")
        return 1
    print("1. Measure: holds.")
    notes = split_notes(read_notes(repo))
    problems, costs = check_account(repo, r, notes)
    if problems:
        print(f"2. Account: OPEN. In {NOTES} under `## account`:")
        print("\n".join("   " + p for p in problems))
        print("CHECKUP-GATE: open")
        return 1
    print("2. Account: holds.")
    notes = split_notes(read_notes(repo))
    problems, risks = check_read(repo, r, notes)
    if problems:
        print(f"3. Read: OPEN. In {NOTES} under `## read`:")
        print("\n".join("   " + p for p in problems))
        print("CHECKUP-GATE: open")
        return 1
    print("3. Read: holds.")
    notes = split_notes(read_notes(repo))
    problems, verdicts, ranked = check_answer(repo, r, notes, costs)
    if problems:
        print(f"4. Answer: OPEN. In {NOTES} under `## answer`:")
        print("\n".join("   " + p for p in problems))
        print("CHECKUP-GATE: open")
        return 1
    print("4. Answer: holds.")
    print()
    print("ANSWER")
    print(measured_line(r))
    for key, title, fixer in SECTIONS:
        sec = r["sections"][key]
        n = sum(1 for f in r["findings"] if f["section"] == key)
        tail = f"not measured: {sec['why']}" if not sec["measured"] else f"{n} finding(s)"
        print(f"- {title}: {verdicts[key]} ({tail})")
    if risks:
        print("Found while reading (not structure; a bug here may come before any fix below):")
        for p, name, what in risks:
            print(f"- {p} {name}(): {what}")
    if ranked:
        print("Fix first:")
        for n, f in enumerate(ranked, 1):
            with_ = f" With {FIXER[f['section']]}." if installed(FIXER[f["section"]]) else ""
            print(f"{n}. {f['detail']} ({f['where']}). Cost: {costs[f['id']]}.{with_}")
    else:
        print("Fix first: nothing measured has a cost.")
    print("CHECKUP-GATE: done")
    return 0


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description="One report on a codebase's structure, ranked by where changes land.")
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true", help="check the four stages")
    ap.add_argument("--fresh", action="store_true", help="ignore the cached report")
    ap.add_argument("--window", type=int, default=WINDOW, help=f"commits of history to read (default {WINDOW})")
    ap.add_argument("--recent", type=int, default=RECENT,
                    help=f"a finding no commit among this many latest touched is idle (default {RECENT})")
    a = ap.parse_args()
    set_history(a.window, a.recent)
    repo = os.path.abspath(a.repo)
    if git(repo, "rev-parse", "--git-dir")[0] != 0:
        print("CHECKUP: blocked (not a git repository: the report counts tracked files and history)")
        return 2
    if a.gate:
        return gate(repo)
    r = load_or_build(repo, a.fresh)
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        print_report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
