#!/usr/bin/env python3
"""features.py — the feature map behind feature-map.

FEATURES.md at the repo root says what the system has and how each feature is reached: route,
click target, shortcut, CLI command. Three commands:

  init   Draft FEATURES.md from the entry points found in the code, one feature per group.
         A draft: the agent names each feature, writes what it does, and labels it. Never
         overwrites an existing FEATURES.md.
  prove  Run a feature's entry point (the command after --) and keep the receipt in
         .features/<feature>.json: the command, its exit code, the tail of its output, and a hash
         of every file the feature names. For what no command can drive, --file records a
         screenshot or saved response by hash, with --note saying what it shows.
  impact Which features a change touches, and the VERIFY.md sections to rerun. Files come from
         `--files a b`, else `git diff` against HEAD (`--base REF`) plus untracked files.
  check  Test the map against the code. STALE: a mapped entry point or trace step the code no
         longer has. BROKEN: a trace step not called from the step before it (comments do not
         count), or a first step neither in nor called from an entry point's file. Then what the
         map does NOT cover: entry points in the code the map lacks (unmapped; `## Not features`
         lists the ones that are not a feature, each with its reason), features with no trace, no
         VERIFY.md link (or no VERIFY.md), no status label, no description. `proven` needs a
         passing receipt for every entry point (else unproven), and is drifted once a file the
         feature names no longer matches the receipt's hash.
         Links to verify-loop: a `proven` feature whose VERIFY.md section has no receipt of its
         check rejecting a wrong product, or failed its last run, is unbacked (read from
         `verify.py status --json` when verify-loop is installed beside this skill); a feature
         file outside its section's `path:` is unfenced, since `run --affected` would not rerun it.

An entry point is `kind: `anchor` @ file :: needle`. The check looks for the needle in the file (or
anywhere in the repo when no file is given) as a whole token, so `pay-btn` is not found in
`pay-btn-v2`. The needle defaults from the anchor by kind; a shortcut with no needle must appear as
the same combo in a quoted string (`Ctrl+Enter` = 'mod+enter', not 'ctrl+shift+enter'). Write
`:: needle` when the default does not fit. A big map is an index: `include: features/<area>.md`
lines, each read in place (paths from the repo root; VERIFY.md includes are followed the same way).
Stdlib only.

FEATURES.md format:

  ## Checkout
  - what: Pay for the cart and get an order id.
  - route: `/checkout` @ src/app.py
  - click: `[data-testid=pay-btn]` @ src/cart.html
  - shortcut: `Ctrl+Enter` @ src/keys.js :: submitOrder
  - cli: `shop checkout` @ cli.py
  - code: src/checkout/
  - trace: `checkout` @ src/app.py > `place_order` @ src/svc.py > `orders` @ src/schema.sql
  - verify: Checkout
  - status: proven: drove /checkout in a browser, order id shown

  ## Not features
  - cli: `debug-dump` @ cli.py: developer dump, hidden from --help

kinds: route (or api), click, shortcut, cli, menu. status: proven | failing | traced | suspected, then how.

Usage:
  python scripts/features.py init   [repo]
  python scripts/features.py prove  [--repo R] --feature NAME [--entry 'kind: anchor'] [--copy] -- <command>
  python scripts/features.py prove  [--repo R] --feature NAME --entry 'kind: anchor' --file F --note TEXT
  python scripts/features.py prove  [--repo R] --feature NAME [--entry 'click: anchor'] --serve 'CMD {port}' --request 'GET /path' ...
  python scripts/features.py check  [repo] [--strict] [--rerun]
  python scripts/features.py gate   [repo]     check --strict --rerun as three stages; FEATURE-GATE: done
  python scripts/features.py impact [repo] [--base REF | --files a b]

Exit: check 0 = nothing stale or broken; 1 = something stale or broken (or --strict and something is
untraced, unmapped, unlinked, unlabeled, undescribed, drifted, unproven, unbacked, unfenced or unannounced;
--rerun and a recorded run that passed fails now);
2 = no FEATURES.md. prove 0 = recorded and the run passed; 1 = recorded, the run failed; 2 = usage.
Summary line:
  FEATURES: <f> features | <e> entry points, <s> stale | <b> broken | <t> untraced | <u> unmapped |
  <v> unlinked | <l> unlabeled | <d> undescribed | <r> drifted | <p> unproven | <k> unbacked |
  <n> unfenced | <a> unannounced | <i> not features [| <g> regressed, with --rerun]
"""
import argparse, contextlib, hashlib, io, json, os, re, shlex, shutil, socket, subprocess, sys, tempfile, time
import urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from _encoding import utf8_streams
except ImportError:  # the single-file copy vendored into a repo's .features/
    def utf8_streams():
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, ValueError, OSError):
                pass

MAP, VERIFY = "FEATURES.md", "VERIFY.md"
# verify-loop's helper, when this skill is installed beside it (the verify-loop plugin ships both).
VERIFY_PY = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                         "verify-loop", "scripts", "verify.py")
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target",
             "vendor", ".tox", ".next", "fixture", "fixtures", "tests", "test", "__tests__", ".features", ".blast", ".mistakes"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".html",
            ".go", ".rs", ".rb", ".php", ".java", ".kt", ".cs"}
MAX_BYTES = 1_000_000
ENTRY_KINDS = {"route", "api", "click", "shortcut", "cli", "menu"}
LABELS = ("proven", "failing", "traced", "suspected")
AGENT_FILES = ("AGENTS.md", "CLAUDE.md")  # loaded by agents at session start: where the map is announced
ANNOUNCE = ("Read FEATURES.md before driving or changing this app. After any change: "
            "`python .features/features.py check --rerun` lists what moved or stopped working since it was proven; "
            "fix those map lines (rename, or status `failing: <error>`), then "
            "`python .features/features.py prove --again` re-records every run. No need to read the script.")
MODS = {"ctrl": "mod", "control": "mod", "cmd": "mod", "command": "mod", "meta": "mod",
        "cmdorctrl": "mod", "commandorcontrol": "mod", "mod": "mod", "super": "mod",
        "option": "alt", "alt": "alt", "shift": "shift"}

# (kind, regex, what group 1 holds). Every hit is one entry point found in code.
DETECT = [
    ("route", r"@\w+\.(?:route|get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]"),
    ("route", r"\b(?:app|router|server|api)\.(?:get|post|put|delete|patch)\(\s*['\"`](/[^'\"`]*)"),
    ("route", r"\bpath\s*(?:==?|:)\s*\{?['\"](/[^'\"]*)['\"]"),
    ("click", r"data-(?:testid|test|cy|qa)\s*=\s*\{?['\"]([\w-]+)['\"]"),
    ("click", r"<button[^>]*\bid\s*=\s*['\"]([\w-]+)['\"]"),
    ("shortcut", r"\baccelerator\s*:\s*['\"]([^'\"]+)['\"]"),
    ("shortcut", r"\b(?:useHotkeys|hotkeys|Mousetrap\.bind|bindKey)\(\s*['\"]([^'\"]+)['\"]"),
    ("cli", r"\badd_parser\(\s*['\"]([\w-]+)['\"]"),
    ("cli", r"@\w+\.command\(\s*['\"]([\w-]+)['\"]"),
    ("cli", r"\.command\(\s*['\"]([\w-]+)[\s'\"<\[]"),
    ("cli", r"\bUse:\s*\"([\w-]+)"),
]
PAGE_FILE = re.compile(r"(?:^|/)(?:app|pages)/(.*?)/?(?:page|index)\.(?:tsx|jsx|js|ts)$")


# ---- needles ------------------------------------------------------------------------------

def norm_combo(text):
    """'CmdOrCtrl+Shift+O' -> 'mod+shift+o': same shortcut however the code spells the modifier."""
    parts = [p.strip().lower() for p in re.split(r"\+|(?<=\w)-(?=\w)", text) if p.strip()]
    mods = sorted({MODS[p] for p in parts[:-1] if p in MODS})
    return "+".join(mods + parts[-1:])


def default_needle(kind, anchor):
    a = anchor.strip()
    if kind in ("route", "api"):
        a = re.sub(r"^(?:GET|POST|PUT|PATCH|DELETE)\s+", "", a)
        a = re.split(r"[:{<\[*]", a)[0].rstrip("/") or "/"
        return a
    if kind == "click":
        m = re.search(r"[=~^$*|]?=\s*['\"]?([^'\"\]]+)", a) if a.startswith("[") else None
        if m:
            return m.group(1)
        return a.lstrip("#.")
    if kind == "cli":
        return a.split()[-1]
    if kind == "shortcut":
        return re.split(r"\+", a)[-1].strip().lower()
    return a


def identity(kind, anchor, needle):
    """What makes two entries the same entry point, so the map can be diffed against the code."""
    if kind in ("route", "api"):
        return ("route", default_needle("route", anchor))
    if kind == "shortcut":
        return ("shortcut", norm_combo(anchor))
    return (kind, needle)


# ---- reading the map ----------------------------------------------------------------------

def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


INCLUDE = re.compile(r"^(?:[-*]\s+)?include:\s*`?([^`\s]+)`?", re.I)


def load(repo, rel, seen=None):
    """A map file's text with every `include: <path>` line replaced by that file's text, so an
    index can list one area file per line. Paths are from the repo root, as in VERIFY.md."""
    seen = set() if seen is None else seen
    full = os.path.normpath(os.path.join(repo, rel))
    if full in seen:
        return ""
    seen.add(full)
    out = []
    for line in read(full).splitlines():
        m = INCLUDE.match(line.strip())
        out.append(load(repo, m.group(1).strip("'\""), seen) if m else line)
    return "\n".join(out)


ENTRY = re.compile(r"^`([^`]+)`(?:\s*@\s*([^\s:]+)(?::(?!:))?)?(?:\s*::\s*(\S+))?\s*(.*)$")
NOT_FEATURES, NOT_BUILT = "not features", "not built"


def parse(text):
    """[{name, what, entries: [(kind, anchor, file, needle)], verify, status, trace, reasons}].
    `## Not features` holds entry points the code declares that are not a feature (a debug command,
    a test-only selector), each with the reason after it; `## Not built` is prose and is skipped."""
    features, cur = [], None
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            cur = {"name": h.group(1), "what": "", "entries": [], "verify": "", "status": "", "trace": "",
                   "reasons": []}
            if h.group(1).lower() != NOT_BUILT:
                features.append(cur)
            continue
        b = re.match(r"^\s*[-*]\s+([A-Za-z][\w-]*):\s*(.*?)\s*$", line)
        if not (b and cur):
            continue
        key, val = b.group(1).lower(), b.group(2)
        if key in ENTRY_KINDS:
            m = ENTRY.match(val)
            if m:
                cur["entries"].append((key, m.group(1), m.group(2) or "", m.group(3) or ""))
                cur["reasons"].append(re.sub(r"^[\s:;,\-–—]+", "", m.group(4)))
        elif key in ("what", "verify", "status", "trace"):
            cur[key] = val if key == "trace" else val.strip("`")
    return features


def split_ignored(features):
    """(real features, the `## Not features` section or None)."""
    real = [f for f in features if f["name"].lower() != NOT_FEATURES]
    ignored = next((f for f in features if f["name"].lower() == NOT_FEATURES), None)
    return real, ignored


def is_todo(s):
    return not s or s.upper().startswith("TODO")


# ---- finding entry points in code ---------------------------------------------------------

def code_files(repo):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if os.path.splitext(f)[1] in CODE_EXT:
                p = os.path.join(root, f)
                if os.path.getsize(p) <= MAX_BYTES:
                    yield os.path.relpath(p, repo).replace("\\", "/"), p


def discover(repo):
    """[(kind, anchor, file)] for every entry point the code declares."""
    found, seen = [], set()

    def add(kind, anchor, rel):
        key = (kind, anchor, rel)
        if key not in seen:
            seen.add(key)
            found.append(key)

    for rel, path in code_files(repo):
        m = PAGE_FILE.search(rel)
        if m:
            add("route", "/" + re.sub(r"\([^)]*\)/?", "", m.group(1)).strip("/"), rel)
        text = read(path)
        for kind, rx in DETECT:
            for hit in re.finditer(rx, text):
                anchor = hit.group(1)
                if kind == "click" and "data-" not in hit.group(0):
                    anchor = "#" + anchor
                elif kind == "click":
                    anchor = f"[data-testid={anchor}]"
                add(kind, anchor, rel)
    return found


# ---- init ---------------------------------------------------------------------------------

def group_of(kind, anchor, rel):
    if kind == "route":
        seg = [s for s in anchor.strip("/").split("/") if s and s != "api" and not re.match(r"[:{<\[]", s)]
        return seg[0].replace("-", " ").title() if seg else "Home"
    if kind == "cli":
        return anchor.replace("-", " ").title()
    return re.sub(r"\.\w+$", "", rel.rsplit("/", 1)[-1]).replace("_", " ").replace("-", " ").title()


def cmd_init(repo):
    path = os.path.join(repo, MAP)
    if os.path.exists(path):
        print(f"{MAP} already exists at {path}; not overwriting. Edit it, or delete it first.")
        return 2
    groups = {}
    for kind, anchor, rel in discover(repo):
        groups.setdefault(group_of(kind, anchor, rel), []).append((kind, anchor, rel))
    out = [
        "# FEATURES", "",
        "What the system has and how each feature is reached. The commands that keep it true need",
        "no skill installed; their `--help` says the rest, so the script never needs reading:",
        f"- `python {PROOFS}/features.py check --rerun`: every entry point against the code, and every",
        f"  recorded run ({PROOFS}/<feature>.json) run again, naming what moved or stopped working.",
        f"- `python {PROOFS}/features.py prove --feature \"<name>\" [--copy] -- <command>`: run an entry",
        "  point and record it (`--copy` runs it in a throwaway copy, for anything that writes data).",
        f"- `python {PROOFS}/features.py prove --feature \"<name>\" --serve \"<start cmd with {{port}}>\" --request",
        "  \"GET /path\"`: the same for a web route, served from a throwaway copy.",
        "- status: `proven` (a passing run is recorded), `failing` (a failing run is recorded), `traced`",
        "  (read start to end, not run) or `suspected`, then how you know.",
        "- format: entry lines are ``kind: `anchor` @ file :: needle`` (kinds route, click, shortcut, cli,",
        "  menu; the needle, found in the file as a whole token, defaults from the anchor). A trace is",
        "  steps ``symbol` @ file`` joined by ` > `, each named in the step before; a page reaches the",
        "  server by the path it sends (`/api/x` @ server.py). `## Not features` lists entry lines that",
        "  are not features, each with `: <reason>`; `## Not built` is prose for what the code lacks.",
        "  Past ~150 lines, keep this file as `- include: features/<area>.md` lines.", "",
        "This draft was found from the code: regroup by real feature, write what each does, add the",
        "entry points a scan cannot see, label each, and replace every TODO.", "",
    ]
    for name in sorted(groups):
        out.append(f"## {name}")
        out.append("- what: TODO one sentence: what this feature does for its user")
        for kind, anchor, rel in groups[name]:
            out.append(f"- {kind}: `{anchor}` @ {rel}")
        out.append("- trace: TODO `handler` @ file > `what it calls` @ file > `effect` @ file")
        out.append("- verify: TODO name of the VERIFY.md section that proves it")
        out.append("- status: TODO proven | traced | suspected, then how you know")
        out.append("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    vendor(repo)
    n = sum(len(v) for v in groups.values())
    print(f"wrote {path}: {len(groups)} group(s), {n} entry point(s) found in code." +
          ("" if n else " None found; add a '## <feature>' section per feature by hand."))
    return 0


# ---- git: what changed, what a feature owns ------------------------------------------------

def git_lines(repo, *args):
    """Output lines of a git command run in repo, or None when git or the repo is unavailable."""
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")
    except OSError:
        return None
    return r.stdout.splitlines() if r.returncode == 0 else None


def changed_files(repo, ref):
    """Files changed against ref (working tree included) plus untracked ones; None if git fails."""
    diff = git_lines(repo, "diff", "--name-only", "--relative", ref)
    if diff is None:
        return None
    return set(diff) | set(git_lines(repo, "ls-files", "--others", "--exclude-standard") or [])


def feature_files(f):
    """Every file a feature's map names: entry-point files and trace steps."""
    files = {rel for _k, _a, rel, _n in f["entries"] if rel}
    for raw in f["trace"].split(" > "):
        m = STEP.match(raw.strip())
        if m and m.group(2):
            files.add(m.group(2))
    return files


def cmd_impact(repo, files, base):
    features, _ = split_ignored(parse(load(repo, MAP)))
    if not features:
        print(f"no {MAP} with features in {repo}; run `features.py init`.")
        return 2
    changed = set(f.replace("\\", "/") for f in files) if files else changed_files(repo, base)
    if changed is None:
        print(f"cannot read the change from git in {repo}; pass --files a b.")
        return 2
    claimed = set()
    hit = 0
    for f in features:
        own = feature_files(f)
        touched = sorted(own & changed)
        claimed |= own
        if touched:
            hit += 1
            print(f["name"])
            print("  changed: " + ", ".join(touched))
            print(f"  verify: {f['verify'] if not is_todo(f['verify']) else 'none linked, no check to rerun'}")
    loose = sorted(c for c in changed if os.path.splitext(c)[1] in CODE_EXT and c not in claimed)
    if loose:
        print("Changed code claimed by no feature (map gap, or shared code to check by hand):")
        for c in loose:
            print(f"  {c}")
    print(f"IMPACT: {len(changed)} changed file(s) | {hit} feature(s) affected | {len(loose)} claimed by no feature")
    return 0


# ---- prove: a receipt of running an entry point --------------------------------------------

PROOFS = ".features"
TAIL = 20


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "feature"


def file_sha(path):
    """sha256 of a file with line endings normalized, so a checkout's CRLF is not a change."""
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read().replace(b"\r\n", b"\n")).hexdigest()
    except OSError:
        return None


def entry_label(kind, anchor):
    return f"{'route' if kind == 'api' else kind}: {anchor}"


def load_proof(repo, name):
    try:
        with open(os.path.join(repo, PROOFS, slug(name) + ".json"), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data.get("runs"), list) else {"runs": []}
    except (OSError, ValueError, AttributeError):
        return {"runs": []}


def live_runs(repo, f):
    """The feature's receipts, each narrowed to entry points the map still has; a run for a
    renamed or removed entry point is history, not proof, and is neither checked nor re-run."""
    have = {entry_label(k, a) for k, a, _r, _n in f["entries"]}
    out = []
    for r in load_proof(repo, f["name"])["runs"]:
        keep = [e for e in r.get("entries", []) if e in have]
        if keep:
            out.append({**r, "entries": keep})
    return out


def named_in(kind, anchor, needle, text):
    """Whether a command line or note names the entry point (its needle as a whole token)."""
    if kind in ("route", "api"):  # a route is hit by a path in the command, never by its needle as a word
        return any(route_matches(anchor, p) for p in re.findall(r"(/[^\s'\"`]*)", text))
    n = needle or default_needle(kind, anchor)
    if kind == "shortcut" and not needle:
        return norm_combo(anchor) in {norm_combo(t) for t in re.findall(r"[\w+-]+", text)}
    return has_token(text, n) if n != "/" else "/" in text


def vendor(repo):
    """Copy this checker into the repo's .features/, so a later session or CI can run
    `python .features/features.py check --rerun` without the skill installed."""
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(repo, PROOFS)
    if os.path.normcase(os.path.normpath(here)) == os.path.normcase(os.path.normpath(dest)):
        return
    os.makedirs(dest, exist_ok=True)
    src, copy = os.path.abspath(__file__), os.path.join(dest, "features.py")
    if file_sha(src) != file_sha(copy):
        shutil.copyfile(src, copy)


def execute(repo, command, timeout, in_copy):
    """(exit code, output) of command run in repo, or in a throwaway copy of it when in_copy, so
    an entry point that writes never touches the real data. Local paths become <repo>."""
    tmp = tempfile.mkdtemp(prefix="features-prove-") if in_copy else None
    where = os.path.join(tmp, "repo") if tmp else repo
    try:
        if tmp:
            shutil.copytree(repo, where, ignore=shutil.ignore_patterns(".git", PROOFS, "__pycache__"))
        try:
            p = subprocess.run(command, cwd=where, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout)
            code, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired as e:
            code, out = "timeout", str(e)
        except OSError as e:
            code, out = "not run", str(e)
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
    for root in (where, repo):
        for form in {root, root.replace("\\", "/"), root.replace("/", "\\")}:
            out = out.replace(form, "<repo>")  # receipts are committed: no local paths
    return code, out


def route_matches(anchor, path):
    """Whether a request path hits a route anchor: `<id>`, `{id}`, `:id` and `*` match one segment."""
    pattern = re.sub(r"<[^>/]+>|\\\{[^}/]+\\\}|:\w+|\\\*", "[^/]+", re.escape(anchor.split("?")[0]))
    return re.fullmatch(pattern, path.split("?")[0]) is not None


def literal_prefix(path):
    """The request path up to its first segment that names a record (a number), e.g. /api/items/."""
    out = ""
    for seg in path.split("?")[0].strip("/").split("/"):
        if seg.isdigit():
            return out + "/"
        out += "/" + seg
    return out


def serve_and_request(repo, serve, requests, timeout):
    """(exit code, output) of starting `serve` (its `{port}` filled with a free port) in a throwaway
    copy of the repo, sending each `METHOD /path [json body]`, then stopping it. Exit 0 only when
    every request got a status below 400. The server's own output is kept: a traceback lands there."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    tmp = tempfile.mkdtemp(prefix="features-serve-")
    where = os.path.join(tmp, "repo")
    lines, code, proc, log, server = [], 0, None, None, []
    try:
        shutil.copytree(repo, where, ignore=shutil.ignore_patterns(".git", PROOFS, "__pycache__"))
        log = open(os.path.join(tmp, "server.log"), "w+", encoding="utf-8", errors="replace")
        argv = [sys.executable if a == "python" else a for a in shlex.split(serve.replace("{port}", str(port)))]
        proc = subprocess.Popen(argv, cwd=where, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.time() + min(timeout, 30)
        while time.time() < deadline and proc.poll() is None:
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.5).close()
                break
            except OSError:
                time.sleep(0.2)
        else:
            code = 1
            lines.append(f"server did not listen on port {port}" + (f" (exit {proc.returncode})" if proc.poll() is not None else ""))
        for req in requests if code == 0 else []:
            method, _, rest = req.strip().partition(" ")
            path, _, body = rest.strip().partition(" ")
            data = body.strip().encode("utf-8") if body.strip() else None
            r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data, method=method.upper(),
                                       headers={"Content-Type": "application/json"} if data else {})
            try:
                with urllib.request.urlopen(r, timeout=timeout) as resp:
                    status, text = resp.status, resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                status, text = e.code, e.read().decode("utf-8", "replace")
            except (urllib.error.URLError, OSError) as e:
                status, text = "no response", str(getattr(e, "reason", e))
            if not isinstance(status, int) or status >= 400:
                code = 1
            lines.append(f"{method.upper()} {path} -> {status} {' '.join(text.split())[:200]}")
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(5)
            except subprocess.TimeoutExpired:
                proc.kill()
        if log:
            log.seek(0)
            server = log.read().strip().splitlines()
            log.close()
        shutil.rmtree(tmp, ignore_errors=True)
    out = "\n".join(lines + ([f"server: {x}" for x in server[-12:]] if server else []))
    for form in {where, where.replace("\\", "/"), repo, repo.replace("\\", "/")}:
        out = out.replace(form, "<repo>")
    return code, out


def cmd_prove(repo, name, command, shot, wanted, note, timeout, in_copy=False, serve=None, requests=None):
    features, _ = split_ignored(parse(load(repo, MAP)))
    f = next((x for x in features if x["name"].lower() == (name or "").lower()), None)
    if not f:
        print(f"no feature '{name}' in {MAP}. Features: " + ", ".join(x["name"] for x in features))
        return 2
    labels = {entry_label(k, a): (k, a, r, n) for k, a, r, n in f["entries"]}
    via = []
    if serve:
        if "{port}" not in serve or not requests:
            print("--serve needs the command that starts the app with `{port}` where the port goes "
                  "(e.g. --serve \"python app.py --port {port}\") and at least one --request \"GET /path\".")
            return 2
        paths = [r.strip().partition(" ")[2].strip().partition(" ")[0] for r in requests]
        covers = [lab for lab, (k, a, _r, _n) in labels.items()
                  if k in ("route", "api") and any(route_matches(a, p) for p in paths)]
        route_files = {r for lab, (k, _a, r, _n) in labels.items() if lab in covers and r}
        trace_files = {m for m in re.findall(r"`[^`]+`\s*@\s*([^\s>]+)", f["trace"] or "")} - route_files
        for w in wanted or []:
            if w not in labels:
                print(f"not an entry point of '{f['name']}': {w}. Its entry points: " + "; ".join(labels))
                return 2
            k, a, rel, _n = labels[w]
            if k in ("route", "api"):
                covers.append(w)
                continue
            files = ({rel} if rel else set()) | trace_files
            hits = [p for p in paths if len(literal_prefix(p)) > 1 and any(
                literal_prefix(p).rstrip("/") in read(os.path.join(repo, x)) for x in files)]
            if not hits:
                wanted_text = ", ".join(sorted({literal_prefix(p).rstrip("/") for p in paths}))
                print(f"{w}: looked for {wanted_text} in {', '.join(sorted(files)) or 'no file'} and found none. "
                      "A page control is proven through a route only when its own file, or a trace step not in "
                      "the route's file, contains the path it sends: add that step to the feature's trace "
                      "(e.g. `handler` @ app.js), or leave the control read, not run.")
                return 2
            covers.append(w)
            via.append(w)
        if not covers:
            print(f"the requests hit none of the routes of '{f['name']}' ({'; '.join(labels)}); name the "
                  "route in the map, or --entry \"route: <anchor>\".")
            return 2
        covers = list(dict.fromkeys(covers))
    elif wanted:
        unknown = [w for w in wanted if w not in labels]
        if unknown:
            print(f"not an entry point of '{f['name']}': {', '.join(unknown)}. Its entry points: "
                  + "; ".join(labels))
            return 2
        covers = list(wanted)
    elif command:
        line = " ".join(command)
        covers = [lab for lab, (k, a, _r, n) in labels.items() if named_in(k, a, n, line)]
        if not covers:
            print(f"the command names none of the entry points of '{f['name']}' ({'; '.join(labels)}). "
                  "A command proves an entry point when it contains its word (cli: the subcommand, route: "
                  "the path); otherwise name it with --entry \"kind: anchor\" as written in the map.")
            return 2
    else:
        print("prove what? Pass the command to run after --, or --file with --entry and --note.")
        return 2

    run = {"entries": covers, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "note": note or ""}
    if shot:
        full = os.path.abspath(os.path.join(repo, shot))
        if not note or not os.path.isfile(full) or not full.startswith(os.path.abspath(repo) + os.sep):
            print("--file needs a file inside the repo (a screenshot, a saved response) and a --note "
                  "saying what it shows.")
            return 2
        run.update(kind="file", file=os.path.relpath(full, repo).replace("\\", "/"), file_sha=file_sha(full))
        code = 0
    elif serve:
        code, out = serve_and_request(repo, serve, requests, timeout)
        lines = out.rstrip().splitlines()
        run.update(kind="run", command=f"serve: {serve} | " + " ; ".join(requests), serve=serve,
                   requests=list(requests), via_route=via, in_copy=True, exit=code, output_tail=lines[-TAIL:],
                   output_sha=hashlib.sha256(out.encode("utf-8")).hexdigest(), output_lines=len(lines))
    else:
        code, out = execute(repo, command, timeout, in_copy)
        lines = out.rstrip().splitlines()
        run.update(kind="run", command=" ".join(command), argv=command, in_copy=in_copy, exit=code,
                   output_tail=lines[-TAIL:],
                   output_sha=hashlib.sha256(out.encode("utf-8")).hexdigest(), output_lines=len(lines))
    run["files"] = {rel: file_sha(os.path.join(repo, rel)) for rel in sorted(feature_files(f))}

    proof = load_proof(repo, f["name"])
    kept = []
    for old in proof["runs"]:
        # an entry point the map no longer has (renamed, removed) takes its old receipt with it
        old["entries"] = [e for e in old.get("entries", []) if e not in covers and e in labels]
        if old["entries"]:
            kept.append(old)
    proof = {"feature": f["name"], "runs": kept + [run]}
    vendor(repo)
    dest = os.path.join(repo, PROOFS, slug(f["name"]) + ".json")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(proof, fh, indent=2)
        fh.write("\n")
    rel = os.path.relpath(dest, repo).replace("\\", "/")
    if code != 0:
        print(f"recorded in {rel}: {'; '.join(covers)} FAILED (exit {code}). Not proof: report it as a "
              "finding, and do not label the feature proven.")
        for line in run.get("output_tail", [])[-5:]:
            print(f"  | {line}")
        return 1
    print(f"recorded in {rel}: {'; '.join(covers)} " + ("ran, exit 0" if run["kind"] == "run" else f"shown in {run['file']}"))
    left = [lab for lab in labels if not any(lab in r["entries"] for r in proof["runs"])]
    if left:
        print("  not yet proven: " + "; ".join(left))
    return 0


def cmd_again(repo, name, timeout):
    """Re-run every recorded command (of one feature, or all) and record the result in place of
    the old receipt: a passing run is re-pinned to the code as it is now, a failing one is kept as
    failing. Screenshots cannot be re-taken here; they are listed for a person or agent to redo."""
    features, _ = split_ignored(parse(load(repo, MAP)))
    if name:
        features = [f for f in features if f["name"].lower() == name.lower()]
        if not features:
            print(f"no feature '{name}' in {MAP}")
            return 2
    worst = 0
    for f in features:
        for r in live_runs(repo, f):
            if r.get("kind") == "run" and r.get("serve"):
                code = cmd_prove(repo, f["name"], None, None, r.get("entries"), r.get("note"), timeout,
                                 serve=r["serve"], requests=r.get("requests"))
                worst = max(worst, code)
            elif r.get("kind") == "run" and r.get("argv"):
                code = cmd_prove(repo, f["name"], r["argv"], None, r.get("entries"), r.get("note"),
                                 timeout, r.get("in_copy", False))
                worst = max(worst, code)
            elif r.get("kind") == "file":
                print(f"{f['name']}: {'; '.join(r.get('entries', []))} was shown in {r.get('file')}; "
                      "drive it again and record a new --file")
    return worst


def proof_problems(repo, f):
    """(unproven reasons, drifted reasons) for a feature labelled proven: every entry point needs a
    receipt from `prove` whose run passed, and every file the feature names must be unchanged
    since that receipt."""
    runs = live_runs(repo, f)
    me = f"python {os.path.abspath(__file__)} prove --repo {repo} --feature \"{f['name']}\""
    unproven, drifted = [], []
    if not runs:
        unproven.append(f"proven, but no receipt in {PROOFS}/{slug(f['name'])}.json")
    ran = any(r.get("kind") == "run" and r.get("exit") == 0 for r in runs)
    for k, a, _r, _n in f["entries"]:
        lab = entry_label(k, a)
        if ran and k in ("click", "shortcut", "menu"):
            continue  # a control that sends no request is read, not run; the Proof line says so
        if not any(lab in r.get("entries", []) for r in runs):
            how = (f"--entry \"{lab}\" -- <the command that drives it>" if k == "cli"
                   else f"--entry \"{lab}\" -- <the command that drives it>, or --serve \"<start command with "
                        f"{{port}}>\" --request \"GET {a}\"" if k in ("route", "api")
                   else f"--entry \"{lab}\" --serve \"<start command with {{port}}>\" --request \"<the request it "
                        f"sends>\" (proven through the route it calls), or --file <screenshot> --note \"<what it shows>\"")
            unproven.append(f"{lab} has no receipt; to prove it: {me} {how}")
    for r in runs:
        what = "; ".join(r.get("entries", []))
        if r.get("kind") == "file":
            if file_sha(os.path.join(repo, r.get("file", ""))) != r.get("file_sha"):
                unproven.append(f"{what}: {r.get('file')} is missing or not the file that was recorded")
        elif r.get("exit") != 0:
            unproven.append(f"{what}: its run exited {r.get('exit')}")
        moved = sorted(rel for rel in feature_files(f)
                       if rel not in r.get("files", {}) or file_sha(os.path.join(repo, rel)) != r["files"][rel])
        if moved:
            drifted.append(f"{', '.join(moved)} changed since {what} was proven ({r.get('at', '?')})")
    return unproven, sorted(set(drifted))


# ---- check --------------------------------------------------------------------------------

QUOTED = re.compile(r"['\"`]([^'\"`\n]{1,40})['\"`]")


def has_token(text, needle):
    """needle in text as a whole token: `pay-btn` is not in `pay-btn-v2`, `place_order` not in
    `place_orders`."""
    return re.search(rf"(?<![\w$-]){re.escape(needle)}(?![\w$-])", text) is not None


def found(kind, anchor, needle, text):
    """Whether text still declares the entry point. A shortcut without its own `:: needle` must
    appear as the same combo, so `Ctrl+Enter` is not satisfied by `ctrl+shift+enter`."""
    if kind == "shortcut" and not needle:
        combo = norm_combo(anchor)
        return any(norm_combo(q) == combo for q in QUOTED.findall(text))
    if kind == "cli" and not needle:
        # a subcommand is declared as a name in quotes ("search", 'search <q>') or by a function
        # a decorator names it after; the word as a module or variable (`search.run`) is not one.
        n = re.escape(default_needle(kind, anchor))
        return re.search(rf"['\"`]{n}(?:\s[^'\"`\n]*)?['\"`]|\bdef\s+{n}\s*\(", text) is not None
    return has_token(text, needle or default_needle(kind, anchor))


def stale_reason(repo, kind, anchor, rel, needle, cache):
    """None when the entry point still exists, else why not."""
    shown = needle or (anchor if kind == "shortcut" else default_needle(kind, anchor))
    if rel:
        p = os.path.join(repo, rel)
        if not os.path.isfile(p):
            return f"{rel} does not exist"
        if kind in ("route", "api") and not needle:
            route = default_needle(kind, anchor).strip("/")
            if not route or f"/{route}/" in f"/{rel}":
                return None
        return None if found(kind, anchor, needle, read(p)) else f"'{shown}' not found in {rel}"
    for r, p in code_files(repo):
        if found(kind, anchor, needle, cache.setdefault(r, read(p))):
            return None
    return f"'{shown}' not found anywhere in the code"


STEP = re.compile(r"^`([^`]+)`(?:\s*@\s*(\S+))?(?:\s*::\s*(\S+))?")
COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->|(?:^|\s)(?:#|//)[^\n]*", re.S | re.M)


def uses(text, needle):
    """How often code (comments stripped) names needle as a whole token."""
    return len(re.findall(rf"(?<![\w$]){re.escape(needle)}(?![\w$])", COMMENT.sub(" ", text)))


def trace_problems(repo, trace, entry_files=()):
    """[(tag, message)]: STALE when a step is not in its file, BROKEN when a step is not
    referenced from the step before it (the path is no longer a real call chain), or when the
    first step is neither in an entry point's file nor called from one (the path starts somewhere
    the user cannot reach)."""
    out, prev_rel, prev_text = [], None, ""
    entry_files = [r for r in entry_files if os.path.isfile(os.path.join(repo, r))]
    for i, raw in enumerate(trace.split(" > ")):
        m = STEP.match(raw.strip())
        if not m:
            out.append(("STALE", f"unreadable step: {raw.strip()[:40]}"))
            continue
        sym, rel, needle = m.group(1), m.group(2) or "", m.group(3) or m.group(1)
        if not m.group(3) and sym.startswith("/") and re.search(r"<|\{|:\w|\*", sym):
            # a parameterised route: the code holds its fixed part (`/api/items/${id}/use`, a regex)
            needle = re.split(r"/?(?:<|\{|:\w|\*)", sym, 1)[0].rstrip("/") or sym
        text = read(os.path.join(repo, rel)) if rel else ""
        if not rel or not os.path.isfile(os.path.join(repo, rel)):
            out.append(("STALE", f"{sym}: {rel or 'no file given'} does not exist"))
            prev_rel, prev_text = None, ""
            continue
        if needle not in text:
            out.append(("STALE", f"{sym}: '{needle}' not found in {rel}"))
            prev_rel, prev_text = None, ""
            continue
        if prev_rel is not None:
            defined = re.search(rf"\b(?:def|function|func|fn|class|const|let|var)\s+{re.escape(needle)}\b", text)
            need = 2 if rel == prev_rel and defined else 1
            if uses(prev_text, needle) < need:
                hop = ("; a page reaches the server by a request, so name that step by the path it sends "
                       f"(`/api/...` @ {rel})" if os.path.splitext(prev_rel)[1] in (".js", ".jsx", ".ts", ".tsx", ".html", ".vue", ".svelte", ".mjs")
                       and os.path.splitext(rel)[1] not in (".js", ".jsx", ".ts", ".tsx", ".html", ".vue", ".svelte", ".mjs") else "")
                out.append(("BROKEN", f"{sym} is not called from {prev_rel}{hop}"))
        elif i == 0 and entry_files and rel not in entry_files and not any(
                uses(read(os.path.join(repo, e)), needle) for e in entry_files):
            out.append(("BROKEN", f"{sym}, the first step, is not reached from the entry point file "
                                  f"({', '.join(sorted(set(entry_files)))})"))
        prev_rel, prev_text = rel, text
    return out


def verify_paths(vtext):
    """{section name lower: [path: entries]} from VERIFY.md text, as verify.py reads them."""
    paths, cur = {}, None
    for line in vtext.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            cur = paths.setdefault(h.group(1).lower(), [])
            continue
        b = re.match(r"^\s*[-*]\s+paths?:\s*(.*?)\s*$", line, re.I)
        if b and cur is not None:
            cur.extend(p.strip().strip("`").removeprefix("./") for p in b.group(1).split(",") if p.strip())
    return paths


def unfenced_reason(f, paths):
    """None when every file the feature names is inside its VERIFY.md section's `path:`, so
    `verify.py run --affected` reruns the check when any of them changes; else why not."""
    if not paths:
        return f"'{f['verify']}' in {VERIFY} has no path:, so `verify.py run --affected` cannot tie this feature's files to it"
    inside = lambda rel: any(rel == p.rstrip("/") or rel.startswith(p.rstrip("/") + "/") for p in paths)
    out = sorted(rel for rel in feature_files(f) if not inside(rel))
    if out:
        return (f"{', '.join(out)} outside the path: of '{f['verify']}' in {VERIFY}, so a change there "
                "does not rerun its check")
    return None


def verify_answer(repo):
    """verify-loop's recorded answer for repo (`verify.py status --json`), or None when verify-loop
    is not installed beside this skill or gives no readable answer."""
    if not os.path.isfile(VERIFY_PY):
        return None
    try:
        r = subprocess.run([sys.executable, VERIFY_PY, "status", repo, "--json"],
                           capture_output=True, text=True, encoding="utf-8")
        return json.loads(r.stdout)
    except (OSError, ValueError):
        return None


def unbacked_reason(section, ans):
    """None when verify-loop holds a receipt of the section's check rejecting a wrong product and
    its last run of that check passed; else why `proven` is only a claim."""
    if ans.get("state") == "tampered":
        return f"verify-loop's state is tampered ({ans.get('detail', '')})"
    failing = {k.split("|", 1)[0].lower() for k in ans.get("gaps", {}).get("failing", [])}
    if section.lower() in failing:
        return f"a check of '{section}' failed in the last verify-loop run"
    if section.lower() not in {r.get("feature", "").lower() for r in ans.get("rejections", [])}:
        return (f"no verify-loop receipt shows '{section}' rejecting a wrong product "
                "(`verify.py advance` proves it)")
    return None


def cmd_check(repo, strict, rerun=False):
    path = os.path.join(repo, MAP)
    if not os.path.isfile(path):
        print(f"no {MAP} in {repo}. Run `features.py init` to draft one.")
        return 2
    features, ignored = split_ignored(parse(load(repo, MAP)))
    if not features:
        print(f"{MAP} has no '## <feature>' sections; nothing to check.")
        return 2
    vtext = load(repo, VERIFY)
    vnames = {m.lower(): m for m in re.findall(r"(?m)^##\s+(.+?)\s*$", vtext) if m.lower() not in ("blind spots", "run") and not m.lower().startswith("journey:")}

    vpaths = verify_paths(vtext)
    ans = verify_answer(repo) if vtext and any(f["status"].lower().startswith("proven") for f in features) else None
    if vtext and ans is None and not os.path.isfile(VERIFY_PY):
        print("note  receipts not checked: verify-loop is not installed beside feature-map, "
              "so `proven` is taken on its word")

    cache, mapped = {}, set()
    entries = stale = broken = untraced = unlinked = unlabeled = undescribed = drifted = unproven = 0
    unbacked = unfenced = regressed = 0
    for f in features:
        print(f["name"])
        for kind, anchor, rel, needle in f["entries"]:
            entries += 1
            mapped.add(identity(kind, anchor, needle or default_needle(kind, anchor)))
            why = stale_reason(repo, kind, anchor, rel, needle, cache)
            stale += bool(why)
            where = f" @ {rel}" if rel else ""
            print(f"  {'STALE' if why else 'ok   '}  {kind}  {anchor}{where}" + (f"  ({why})" if why else ""))
        if not f["entries"]:
            print("  note  no entry points: how does a user reach this?")
        if is_todo(f["trace"]):
            untraced += 1
            print("  note  untraced: no 'trace:' path from entry point to effect")
        else:
            for tag, msg in trace_problems(repo, f["trace"], [r for _k, _a, r, _n in f["entries"] if r]):
                stale += tag == "STALE"
                broken += tag == "BROKEN"
                print(f"  {tag:<5}  trace  {msg}")
        if is_todo(f["what"]):
            undescribed += 1
            print("  note  undescribed: no 'what:' line")
        if is_todo(f["verify"]) and not vtext:
            pass  # no VERIFY.md: the project does not use verify-loop, and the receipts are the proof
        elif is_todo(f["verify"]):
            unlinked += 1
            print("  note  no verify link to a VERIFY.md section")
        elif not vtext:
            unlinked += 1
            print(f"  note  verify: '{f['verify']}' links to no {VERIFY}: there is no {VERIFY} in the repo")
        elif f["verify"].lower() not in vnames:
            unlinked += 1
            print(f"  note  verify: '{f['verify']}' is not a section of {VERIFY}")
        else:
            why = unfenced_reason(f, vpaths.get(f["verify"].lower()))
            if why:
                unfenced += 1
                print(f"  note  unfenced: {why}")
            why = unbacked_reason(f["verify"], ans) if ans and f["status"].lower().startswith("proven") else None
            if why:
                unbacked += 1
                print(f"  note  unbacked: {why}")
        if not f["status"].lower().startswith(LABELS):
            unlabeled += 1
            print("  note  no status label (proven | failing | traced | suspected)")
        if f["status"].lower().startswith("failing") and not any(
                r.get("kind") == "run" and r.get("exit") != 0 for r in live_runs(repo, f)):
            unproven += 1
            print("  note  unproven: failing, but no failed run is recorded; record it with `prove`")
        if f["status"].lower().startswith("proven"):
            why_not, moved = proof_problems(repo, f)
            unproven += bool(why_not)
            drifted += bool(moved)
            for msg in why_not:
                print(f"  note  unproven: {msg}")
            for msg in moved:
                print(f"  note  drifted: {msg}; re-run `features.py prove`, never relabel without running")
        if rerun:
            for r in live_runs(repo, f):
                if r.get("kind") != "run" or not (r.get("argv") or r.get("serve")):
                    continue
                code, out = (serve_and_request(repo, r["serve"], r.get("requests") or [], 120) if r.get("serve")
                             else execute(repo, r["argv"], 120, r.get("in_copy")))
                what = "; ".join(r.get("entries", []))
                last = (out.strip().splitlines() or [""])[-1][:120]
                if r.get("exit") == 0 and code != 0:
                    regressed += 1
                    print(f"  FAILS  {what}: `{r['command']}` passed when proven, exits {code} now ({last})")
                elif r.get("exit") != 0 and code == 0:
                    print(f"  note   {what}: `{r['command']}` failed when recorded, passes now; prove it again")
                else:
                    print(f"  rerun  {what}: exit {code}, as recorded")

    skipped = 0
    if ignored:
        print("Not features")
        for (kind, anchor, rel, needle), reason in zip(ignored["entries"], ignored["reasons"]):
            why = stale_reason(repo, kind, anchor, rel, needle, cache)
            stale += bool(why)
            where = f" @ {rel}" if rel else ""
            if why:
                print(f"  STALE  {kind}  {anchor}{where}  ({why})")
            elif len(reason.split()) < 2:
                print(f"  note  {kind}  {anchor}{where}: no reason given, so it still counts as unmapped")
            else:
                skipped += 1
                mapped.add(identity(kind, anchor, needle or default_needle(kind, anchor)))
                print(f"  ok     {kind}  {anchor}{where}  ({reason})")

    unmapped = []
    for kind, anchor, rel in discover(repo):
        if identity(kind, anchor, default_needle(kind, anchor)) not in mapped:
            unmapped.append((kind, anchor, rel))
    if unmapped:
        print("Unmapped entry points (in the code, not in the map; map each, or list it under "
              "'## Not features' with the reason):")
        for kind, anchor, rel in unmapped:
            print(f"  {kind}  {anchor}  @ {rel}")
    linked = {f["verify"].lower() for f in features}
    orphans = [n for k, n in vnames.items() if k not in linked]
    if orphans:
        print(f"In {VERIFY} but linked from no feature here: " + ", ".join(orphans))
        unlinked += len(orphans)
    ran = {"here": [], "in a throwaway copy": [], "failing": [], "shown in a file": [],
           "through the route it calls": [], "read, not run": []}
    unrun, unexplained = [], []
    for f in features:
        runs = live_runs(repo, f)
        why_not = re.sub(r"^\w+\s*:?\s*", "", f["status"]) if f["status"].lower().startswith(("traced", "suspected")) else ""
        for k, a, _r, _n in f["entries"]:
            lab = entry_label(k, a)
            r = next((r for r in runs if lab in r.get("entries", [])), None)
            where = (None if r is None else "shown in a file" if r.get("kind") == "file"
                     else "failing" if r.get("exit") != 0
                     else "through the route it calls" if lab in r.get("via_route", [])
                     else "in a throwaway copy" if r.get("in_copy") else "here")
            if where is None and k in ("click", "shortcut", "menu") and f["status"].lower().startswith("proven"):
                where = "read, not run"
            (ran[where] if where else unrun).append(f"{a}")
            if where is None and k in ("cli", "route", "api") and len(why_not.split()) < 3:
                unexplained.append(f"{f['name']}: {lab}")
    print("Proof: " + "; ".join([f"ran {w}: {', '.join(v)}" if w not in ("failing", "shown in a file", "read, not run")
                                 else f"{w}: {', '.join(v)}" for w, v in ran.items() if v]
                                + ([f"never run: {', '.join(unrun)}"] if unrun else [])))
    unannounced = int(not any(MAP in t and "features.py check" in t
                              for t in (read(os.path.join(repo, n)) for n in AGENT_FILES)))
    if unannounced:
        print(f"Unannounced: no {' or '.join(AGENT_FILES)} at the repo root points at {MAP} and its check, so the "
              f"next agent will not find the map. Add this line to one of them (create AGENTS.md if neither exists):\n"
              f"  {ANNOUNCE}")

    print(f"FEATURES: {len(features)} features | {entries} entry points, {stale} stale | "
          f"{broken} broken | {untraced} untraced | {len(unmapped)} unmapped | {unlinked} unlinked | {unlabeled} unlabeled | {undescribed} undescribed | {drifted} drifted | {unproven} unproven | {unbacked} unbacked | "
          f"{unfenced} unfenced | {unannounced} unannounced | {skipped} not features"
          + (f" | {regressed} regressed" if rerun else ""))
    COUNTS.clear()
    COUNTS.update(stale=stale, broken=broken, untraced=untraced, unmapped=len(unmapped), unlinked=unlinked,
                  unlabeled=unlabeled, undescribed=undescribed, drifted=drifted, unproven=unproven,
                  unbacked=unbacked, unfenced=unfenced, unannounced=unannounced, regressed=regressed,
                  unexplained=unexplained, verify=bool(vtext))
    if stale or broken or regressed or (strict and (untraced or unmapped or unlinked or unlabeled or undescribed
                                       or drifted or unproven or unbacked or unfenced or unannounced)):
        return 1
    return 0


COUNTS = {}  # what the last cmd_check found, for gate
STAGES = (
    ("1. Inventory", "every entry point in the code is mapped (or a Not feature with its reason), each "
     "feature has what, trace and status, and no line is stale or broken",
     ("stale", "broken", "unmapped", "untraced", "undescribed", "unlabeled")),
    ("2. Run", "every command and route has a receipt from `prove` (passing or failing), or its feature says "
     "`traced: <why it was not run>`; every `proven` claim is backed by receipts that still pass",
     ("unexplained", "unproven", "drifted", "regressed")),
    ("3. Hand off", "AGENTS.md or CLAUDE.md points at the map and its check (and, with a VERIFY.md, every "
     "feature links a section that covers it)", ("unannounced", "unlinked", "unbacked", "unfenced")),
)


def cmd_gate(repo):
    """check --strict --rerun, sorted into the three stages: which is open and what fixes it."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cmd_check(repo, True, rerun=True)
    text = buf.getvalue()
    if code == 2:
        print(text.strip())
        print("FEATURE-GATE: open 1. Inventory (no map yet: `features.py init` drafts one)")
        return 1
    problems, lines, feature = [], text.splitlines(), None
    for i, ln in enumerate(lines):
        if ln and not ln.startswith(" ") and ":" not in ln:
            feature = ln  # a feature heading in check's output
        elif re.match(r"\s*(STALE|BROKEN|FAILS|note)\b", ln):
            problems.append(f"{feature}: {ln.strip()}" if feature else ln.rstrip())
        elif ln.startswith(("Unmapped", "Unannounced", "In VERIFY")):
            feature = None
            problems.append(ln.rstrip())
            if ln.startswith("Unannounced") and i + 1 < len(lines):
                problems.append(lines[i + 1].rstrip())
        elif feature is None and ln.startswith("  ") and "@" in ln:
            problems.append(ln.rstrip())
    if not COUNTS.get("verify"):
        COUNTS.update(unlinked=0, unbacked=0, unfenced=0)
    first_open = None
    for title, holds, keys in STAGES:
        bad = {k: (len(COUNTS[k]) if isinstance(COUNTS.get(k), list) else COUNTS.get(k, 0)) for k in keys}
        bad = {k: v for k, v in bad.items() if v}
        print(f"{'open' if bad else 'ok  '}  {title}: {holds}"
              + (f"  [{', '.join(f'{v} {k}' for k, v in bad.items())}]" if bad else ""))
        if bad and first_open is None:
            first_open = title
    if COUNTS.get("unexplained"):
        problems.append("Not run, and no reason why (prove it, or label the feature `traced: <why not run>`):")
        problems += [f"  {x}" for x in COUNTS["unexplained"]]
    proof = next((ln for ln in text.splitlines() if ln.startswith("Proof:")), "")
    if first_open:
        print("To fix:")
        for ln in problems:
            print(ln)
        print(f"FEATURE-GATE: open {first_open}")
        return 1
    print(proof)
    print("FEATURE-GATE: done (report the Proof line: it says what ran where)")
    return 0


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description="Feature map: draft FEATURES.md, check it against the code.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="draft FEATURES.md from the entry points found in code")
    i.add_argument("repo", nargs="?", default=".")
    c = sub.add_parser("check", help="test every mapped entry point against the code")
    c.add_argument("repo", nargs="?", default=".")
    c.add_argument("--strict", action="store_true",
                   help="also exit 1 on untraced, unmapped, unlinked, unlabeled, undescribed, drifted, unpinned, "
                        "unbacked or unfenced")
    c.add_argument("--rerun", action="store_true",
                   help="re-run every recorded proof command; exit 1 if one that passed fails now")
    m = sub.add_parser("impact", help="which features a change touches and which VERIFY.md sections to rerun")
    m.add_argument("repo", nargs="?", default=".")
    m.add_argument("--files", nargs="+", help="changed files (default: git diff against --base, plus untracked)")
    m.add_argument("--base", default="HEAD", help="git ref to diff against (default HEAD)")
    p = sub.add_parser("prove", help="run a feature's entry point (or record a screenshot) as its receipt")
    p.add_argument("--repo", default=".")
    p.add_argument("--feature", help="the feature's ## name in FEATURES.md (required, except with --again)")
    p.add_argument("--again", action="store_true",
                   help="re-run every recorded command (all features, or --feature) and re-record each")
    p.add_argument("--entry", action="append", help="'kind: anchor' this proves (default: those the command names)")
    p.add_argument("--file", help="a screenshot or saved response inside the repo, for what no command can drive")
    p.add_argument("--note", help="what the run or file shows (required with --file)")
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--copy", action="store_true",
                   help="run in a throwaway copy of the repo, for an entry point that writes data")
    p.add_argument("--serve", help="start the app with this command (`{port}` is filled with a free port) in "
                   "a throwaway copy, send each --request, then stop it: proves the routes the requests hit, "
                   "and with --entry a page control whose code sends that request")
    p.add_argument("--request", action="append", help="'METHOD /path [json body]' sent to the --serve app")
    g = sub.add_parser("gate", help="check --strict --rerun as three stages: which is open and what fixes it")
    g.add_argument("repo", nargs="?", default=".")
    p.add_argument("command", nargs=argparse.REMAINDER, help="-- then the command that drives the entry point")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    if a.cmd == "init":
        sys.exit(cmd_init(repo))
    if a.cmd == "prove":
        if a.again:
            sys.exit(cmd_again(repo, a.feature, a.timeout))
        if not a.feature:
            ap.error("prove needs --feature (or --again)")
        cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
        sys.exit(cmd_prove(repo, a.feature, cmd, a.file, a.entry, a.note, a.timeout, a.copy,
                           serve=a.serve, requests=a.request))
    if a.cmd == "gate":
        sys.exit(cmd_gate(repo))
    if a.cmd == "impact":
        sys.exit(cmd_impact(repo, a.files, a.base))
    sys.exit(cmd_check(repo, a.strict, a.rerun))


if __name__ == "__main__":
    main()
