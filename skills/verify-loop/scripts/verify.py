#!/usr/bin/env python3
"""verify.py — the feature-to-check map behind verify-loop.

VERIFY.md at the repo root maps each feature to the commands that prove it. Two commands:

  init   Draft VERIFY.md from the test files already on disk, one feature per test file
         (or per feature folder). A draft: the agent fixes the grouping and adds the
         real-run checks. Never overwrites an existing VERIFY.md.
  run    Run every check, print a result per feature, and say what a green run does NOT
         cover: features with no check, checks nobody proved can fail, test files that
         belong to no feature, and the blind spots the recipe lists.

  baseline  Freeze tests, declared oracle files, check commands and the Run recipe. `run` fails
         with CHECK CHANGED if any of them differ: the loop fixes code, never the check.
  status Was the last whole run strict, green and current? One line, exit 0/1/3.
  scope  Before a fix, name the files it may touch. Any later edit outside them fails the run
         (OUT OF SCOPE), and every check that passed when the fix began stays on watch.

`run` also remembers itself in .verify-state.json (gitignore it): it says NEWLY RED when a fix
broke something that passed, SAME FAILURE when a check fails identically twice, and BUDGET after
--budget red runs in a row. A `--only` run compares nothing and saves nothing.
Strict runs require retained failure output for the current checks plus a fail-proof note;
a non-strict pass is partial, never a successful completion status.

A check passes when its command exits 0. Commands run through the shell, like a Makefile:
only run a VERIFY.md from a repo you trust. Stdlib only.

VERIFY.md format:

  ## Feature name
  - test: `python -m pytest tests/test_x.py -q`
  - run: `python app.py --smoke`
  - oracle: SPEC.md, scripts/smoke.py
  - fail-proof: broke the tax rounding, test_x went red, reverted

  ## Journey: Buy something
  - features: Login, Checkout
  - test: `python -m pytest tests/test_buy_flow.py -q`
  - fail-proof: broke the cart handoff, the flow test went red, reverted

  ## Run
  - setup: `python scripts/seed.py`
  - start: `python app.py`
  - ready: `python scripts/wait_http.py http://localhost:8000/health`
  - doctor: `python scripts/check_instance.py`
  - stop: `python scripts/shutdown.py`
  - login: user demo@example.com, password in .env.test

  ## Blind spots
  - the payment gateway is stubbed

A journey is a `## Journey: <name>` section: `features:` lists two or more features that have their
own sections here, and its checks run the whole flow. `## Run` is how to bring the app up: `setup`
(any number, run first), `start` (kept running in the background), `ready` (exits 0 once the app is
up; polled for --timeout seconds), `stop` (optional, else the process tree is killed), `login`
(free text shown to the reader). Checks run only if setup succeeded and the app became ready.

Usage:
  python scripts/verify.py init [repo]
  python scripts/verify.py run  [repo] [--only TEXT] [--timeout 120] [--strict] [--budget 5]
  python scripts/verify.py baseline [repo]
  python scripts/verify.py status   [repo]
  python scripts/verify.py tests    [repo] [--strict]
  python scripts/verify.py scope PATH... [--add | --clear | --check] [--repo .]

Exit: run 0 = no check failed; 1 = a check failed (or --strict and something is unverified or
unproven, or has orphan tests); 2 = no usable VERIFY.md. Summary line:
  VERIFY: <f> features | <p> checks pass, <x> fail | <u> unverified | <n> unproven | <o> orphan tests | <j> journeys, <b> broken
"""
import argparse, ast, fnmatch, hashlib, json, os, re, signal, subprocess, sys, tempfile, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

RECIPE = "VERIFY.md"
GENERIC_DIRS = {"tests", "test", "__tests__", "spec", "specs", "e2e", "integration", "unit"}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target",
             "vendor", ".tox", "fixture", "fixtures"}
TEST_PY = re.compile(r"^(test_.+|.+_test)\.py$")
TEST_JS = re.compile(r"^.+\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$")
TAIL_LINES = 12
STATE = ".verify-state.json"
BUDGET = 5


# ---- reading the recipe -------------------------------------------------------------------

def find_includes(text):
    """List relative paths of included sub-recipes from VERIFY.md text."""
    includes = []
    for line in text.splitlines():
        m = re.match(r"^(?:[-*]\s+)?include:\s*(.+)$", line.strip())
        if m:
            inc = m.group(1).strip().strip("`'\"")
            if inc:
                includes.append(inc)
    return includes


def parse(text, repo=None, seen=None):
    """(features, blind_spots). A feature is {name, checks: [(kind, command)], proofs: [str],
    journey: bool, members: [str], paths: [str]}. The `## Run` section is read by parse_run, not here."""
    features, blind, cur, in_blind = [], [], None, False
    seen = set() if seen is None else seen
    for line in text.splitlines():
        inc = re.match(r"^(?:[-*]\s+)?include:\s*(.+)$", line.strip())
        if inc and not cur and not in_blind:
            inc_path = inc.group(1).strip().strip("`'\"")
            if repo and inc_path:
                full_inc = os.path.normpath(os.path.join(repo, inc_path))
                if full_inc not in seen and os.path.isfile(full_inc):
                    seen.add(full_inc)
                    sub_text = read(repo, inc_path)
                    sub_f, sub_b = parse(sub_text, repo=repo, seen=seen)
                    features.extend(sub_f)
                    blind.extend(sub_b)
            continue
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            title = h.group(1)
            if title.lower() == "blind spots":
                cur, in_blind = None, True
            elif title.lower() == "run":
                cur, in_blind = None, False
            else:
                j = re.match(r"(?i)^journey:\s*(.+)$", title)
                cur = {"name": j.group(1) if j else title, "checks": [], "proofs": [],
                       "journey": bool(j), "members": [], "oracles": [], "signals": [], "paths": []}
                features.append(cur)
                in_blind = False
            continue
        b = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if not b:
            continue
        if in_blind:
            if not b.group(1).upper().startswith("TODO"):
                blind.append(b.group(1))
            continue
        m = re.match(r"^([A-Za-z][\w ./-]*?):\s*(.*)$", b.group(1)) if cur else None
        if not m:
            continue
        kind, val = m.group(1).strip().lower(), m.group(2).strip()
        if len(val) >= 2 and val[0] == val[-1] == "`" and val.count("`") == 2:
            val = val[1:-1]
        if kind in ("fail-proof", "fail proof"):
            if val and not val.upper().startswith("TODO"):
                cur["proofs"].append(val)
        elif kind == "fail-signal":
            if val and not val.upper().startswith("TODO"):
                cur["signals"].append(val)
        elif kind == "features" and cur["journey"]:
            cur["members"] = [m.strip() for m in val.split(",") if m.strip()]
        elif kind == "oracle":
            cur["oracles"].extend(p.strip() for p in val.split(",") if p.strip())
        elif kind in ("path", "paths"):
            cur["paths"].extend(p.strip() for p in val.split(",") if p.strip())
        elif val:
            cur["checks"].append((kind, val))
    return features, blind


def parse_run(text):
    """The `## Run` recipe: {setup: [cmd], start, ready, stop, login}, or None when absent."""
    run, inside, seen = {"setup": []}, False, False
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            inside = h.group(1).lower() == "run"
            seen = seen or inside
            continue
        m = re.match(r"^\s*[-*]\s+([A-Za-z]+):\s*(.*\S)\s*$", line) if inside else None
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2)
        if len(val) >= 2 and val[0] == val[-1] == "`" and val.count("`") == 2:
            val = val[1:-1]
        if key == "setup":
            run["setup"].append(val)
        elif key in ("start", "ready", "doctor", "stop", "login"):
            run[key] = val
    return run if seen else None


# ---- finding tests ------------------------------------------------------------------------

def find_tests(repo):
    found = []
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if TEST_PY.match(f) or TEST_JS.match(f):
                found.append(os.path.relpath(os.path.join(root, f), repo).replace("\\", "/"))
    return sorted(found)


def is_covered(rel, commands, repo):
    """True when some command names this test file, or a directory that holds it."""
    base = rel.rsplit("/", 1)[-1]
    for cmd in commands:
        for tok in re.findall(r"[\w./-]+", cmd.replace("\\", "/")):
            t = tok[2:] if tok.startswith("./") else tok
            t = t.rstrip("/")
            if not t or t == ".":
                continue
            if t in (rel, base) or rel.endswith("/" + t):
                return True
            if rel.startswith(t + "/") and os.path.isdir(os.path.join(repo, t)):
                return True
    return False


def get_affected_files(repo, ref=None):
    """Return set of repo-relative paths changed in git vs ref or uncommitted."""
    changed = set()
    try:
        p = subprocess.run(["git", "-C", repo, "status", "--porcelain"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if p.returncode == 0:
            for line in p.stdout.splitlines():
                if len(line) >= 4:
                    path = line[3:].strip().strip('"').replace("\\", "/")
                    if " -> " in path:
                        path = path.split(" -> ")[-1]
                    changed.add(path)
        if ref:
            p_diff = subprocess.run(["git", "-C", repo, "diff", "--name-only", ref],
                                    capture_output=True, text=True, encoding="utf-8", errors="replace")
            if p_diff.returncode == 0:
                for line in p_diff.stdout.splitlines():
                    if line.strip():
                        changed.add(line.strip().replace("\\", "/"))
    except OSError:
        pass
    return changed


def is_feature_affected(feature, changed_files, repo):
    """True if feature's checks, oracles, declared paths, or test files intersect with changed_files."""
    if not changed_files:
        return True
    all_cmds = [cmd for _, cmd in feature["checks"]]
    for cf in changed_files:
        for p in feature.get("paths", []):
            p_norm = p.rstrip("/").replace("\\", "/")
            if cf == p_norm or cf.startswith(p_norm + "/"):
                return True
        for o in feature["oracles"]:
            o_norm = o.replace("\\", "/")
            if cf == o_norm or cf.endswith("/" + o_norm):
                return True
        if is_covered(cf, all_cmds, repo):
            return True
        base = cf.rsplit("/", 1)[-1]
        for cmd in all_cmds:
            if base in cmd:
                return True
    return False


def filter_affected(features, changed_files, repo):
    affected_names = set()
    for f in features:
        if not f["journey"] and is_feature_affected(f, changed_files, repo):
            affected_names.add(f["name"].lower())
    filtered = []
    for f in features:
        if f["journey"]:
            if any(m.lower() in affected_names for m in f["members"]):
                filtered.append(f)
        elif f["name"].lower() in affected_names:
            filtered.append(f)
    return filtered


# ---- the per-test map ---------------------------------------------------------------------
# `run` maps test FILES to features. A file with forty tests is one row there, so a hollow test
# hides inside a verified feature. `tests` goes down to the function: every test under the
# feature whose command names its file, and the ones that can never go red flagged. Static (it
# parses, it runs nothing), Python only.

ASSERTING = ("assert", "fail", "raises", "warns")


def _call_name(node):
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _asserts(fn, helpers):
    """True if the function has an assertion, directly or by calling a helper that has one."""
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            return True
        if isinstance(n, ast.Call):
            name = _call_name(n)
            if name.lower().startswith(ASSERTING) or name in helpers:
                return True
    return False


def _swallows(fn):
    """A try whose handler only passes, with no failure on the other path: green either way."""
    for n in ast.walk(fn):
        if not isinstance(n, ast.Try):
            continue
        quiet = any(h.body and all(isinstance(b, ast.Pass) or (isinstance(b, ast.Expr)
                    and isinstance(b.value, ast.Constant)) for b in h.body) for h in n.handlers)
        fails = any(isinstance(m, ast.Assert) or (isinstance(m, ast.Call)
                    and _call_name(m).lower().startswith(ASSERTING))
                    for part in (n.body, n.orelse) for st in part for m in ast.walk(st))
        if quiet and not fails:
            return True
    return False


def _skipped(fn):
    names = [n.attr if isinstance(n, ast.Attribute) else n.id for d in fn.decorator_list
             for n in ast.walk(d) if isinstance(n, (ast.Attribute, ast.Name))]
    return any(n.lower().startswith("skip") for n in names)


def tests_in(repo, rel):
    """[(name, flag, skipped)] for the test functions in one Python file; flag is '' or a reason.
    None when the file cannot be parsed."""
    try:
        tree = ast.parse(read(repo, rel))
    except SyntaxError:
        return None
    defs = (ast.FunctionDef, ast.AsyncFunctionDef)
    helpers = set()
    for _ in range(2):
        helpers |= {n.name for n in ast.walk(tree) if isinstance(n, defs)
                    and not n.name.startswith("test") and _asserts(n, helpers)}
    found = []

    def take(fn, name):
        if _swallows(fn):
            flag = "passes either way: it catches the exception and never fails"
        elif not _asserts(fn, helpers):
            flag = "no assertion"
        else:
            flag = ""
        found.append((name, flag, _skipped(fn)))

    for node in tree.body:
        if isinstance(node, defs) and node.name.startswith("test"):
            take(node, node.name)
        elif isinstance(node, ast.ClassDef):
            for m in node.body:
                if isinstance(m, defs) and m.name.startswith("test"):
                    take(m, f"{node.name}.{m.name}")
    return found


def cmd_tests(repo, strict):
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        print(f"no {RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2
    features, _ = parse(read(repo, RECIPE), repo=repo)
    if not features:
        print(f"{RECIPE} has no '## <feature>' sections; nothing to map.")
        return 2
    files = find_tests(repo)
    py = [t for t in files if t.endswith(".py")]
    unread = [t for t in files if not t.endswith(".py")]
    per_file, bad = {}, []
    for t in py:
        got = tests_in(repo, t)
        (bad.append(t) if got is None else per_file.__setitem__(t, got))
    print("Test map: every test under the feature whose command names its file")
    total = mapped = hollow = skipped = 0
    seen = set()

    def show(rel, rows):
        nonlocal total, hollow, skipped
        for name, flag, skip in rows:
            total += 1
            hollow += bool(flag)
            skipped += skip
            marks = [m for m in (flag, "skipped" if skip else "") if m]
            print(f"  {rel}::{name}" + (f"  <- {'; '.join(marks)}" if marks else ""))

    for f in features:
        print(("Journey: " if f["journey"] else "") + f["name"])
        cmds = [c for _, c in f["checks"]]
        mine = [t for t in per_file if is_covered(t, cmds, repo)]
        if not mine:
            print("  (no test functions named by this feature's commands)")
        for t in mine:
            seen.add(t)
            n0 = total
            show(t, per_file[t])
            mapped += total - n0
    loose = [t for t in per_file if t not in seen]
    if loose:
        print("Unmapped (no feature's command names their file):")
        for t in loose:
            show(t, per_file[t])
    for t in bad:
        print(f"note  could not parse {t}; its tests are not counted")
    if unread:
        print(f"note  {len(unread)} JS/TS test file(s) are not itemised: {', '.join(unread)}")
    unmapped = total - mapped
    print(f"TESTS: {total} tests | {mapped} mapped to a feature | {unmapped} unmapped | "
          f"{hollow} without an assertion or a way to fail | {skipped} skipped")
    return 1 if strict and (hollow or unmapped or skipped or bad) else 0


# ---- init ---------------------------------------------------------------------------------

def read(repo, name):
    try:
        with open(os.path.join(repo, name), encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def python_runner(repo):
    """pytest if the project says so, else unittest."""
    if any(os.path.exists(os.path.join(repo, f)) for f in ("pytest.ini", "conftest.py", "tests/conftest.py")):
        return "pytest"
    for f in ("pyproject.toml", "tox.ini", "setup.cfg", "requirements.txt", "requirements-dev.txt"):
        if "pytest" in read(repo, f):
            return "pytest"
    return "unittest"


def suite_command(repo):
    """The whole-suite command for a stack we cannot split per file, or None."""
    pkg = read(repo, "package.json")
    if re.search(r'"test"\s*:', pkg):
        return "npm test"
    if os.path.exists(os.path.join(repo, "go.mod")):
        return "go test ./..."
    if os.path.exists(os.path.join(repo, "Cargo.toml")):
        return "cargo test"
    if re.search(r"(?m)^test\s*:", read(repo, "Makefile")):
        return "make test"
    return None


def feature_name(rel):
    parts = rel.split("/")
    parent = parts[-2] if len(parts) > 1 else ""
    if parent and parent.lower() not in GENERIC_DIRS:
        name = parent
    else:
        name = re.sub(r"\.(test|spec)\.\w+$|\.py$", "", parts[-1])
        name = re.sub(r"^test_|_test$", "", name)
    return name.replace("_", " ").replace("-", " ").title() or rel


def check_for(rel, py_runner, js_splits):
    base = rel.rsplit("/", 1)[-1]
    if TEST_PY.match(base):
        if py_runner == "pytest":
            return f"python -m pytest {rel} -q"
        return f"python -m unittest discover -s {os.path.dirname(rel) or '.'} -p {base}"
    return f"npm test -- {rel}" if js_splits else None


def cmd_init(repo):
    path = os.path.join(repo, RECIPE)
    if os.path.exists(path):
        print(f"{RECIPE} already exists at {path}; not overwriting. Edit it, or delete it first.")
        return 2
    tests = find_tests(repo)
    py_runner = python_runner(repo)
    js_splits = bool(re.search(r"jest|vitest", read(repo, "package.json")))
    groups, unsplit = {}, []
    for rel in tests:
        cmd = check_for(rel, py_runner, js_splits)
        if cmd:
            groups.setdefault(feature_name(rel), []).append(cmd)
        else:
            unsplit.append(rel)
    suite = suite_command(repo)
    if unsplit and suite:
        groups.setdefault("Suite (split into features)", []).append(suite)

    out = [
        "# VERIFY",
        "",
        "Each feature lists the commands that prove it. A check passes when its command exits 0.",
        "Run them all with `verify.py run`. This is a draft: fix the grouping, add a real-run check",
        "for each feature, and replace every TODO. Start with the current task; a complete map",
        "is optional. Unchecked sections remain unverified, and a draft is never proof.",
        "",
    ]
    for name in sorted(groups):
        out.append(f"## {name}")
        for cmd in groups[name]:
            out.append(f"- test: `{cmd}`")
        out.append("- fail-proof: TODO break this feature on purpose, see a check go red, note what you broke")
        out.append("")
    out += ["## Blind spots", "- TODO what these checks do not cover (stubbed services, scale, real data)", ""]
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out))
    n = len(groups)
    print(f"wrote {path}: {n} feature(s) from {len(tests)} test file(s)." +
          ("" if n else " No tests found; add a '## <feature>' section per feature by hand."))
    return 0


def cmd_scaffold_driver(repo, driver_type):
    """Scaffold a real smoke driver (scripts/smoke_driver.py) and .verify-evidence directory."""
    evidence_dir = os.path.join(repo, ".verify-evidence")
    os.makedirs(evidence_dir, exist_ok=True)
    scripts_dir = os.path.join(repo, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    target = os.path.join(scripts_dir, "smoke_driver.py")

    if os.path.exists(target):
        print(f"Driver already exists at {target}; not overwriting.")
        return 1

    driver_type = (driver_type or "auto").lower()
    if driver_type == "auto":
        if os.path.exists(os.path.join(repo, "package.json")):
            driver_type = "web"
        elif any(os.path.exists(os.path.join(repo, f)) for f in ("main.py", "app.py", "server.py")):
            driver_type = "api"
        else:
            driver_type = "cli"

    content = f'''#!/usr/bin/env python3
"""smoke_driver.py — Automated runtime verification driver.
Saves execution evidence into .verify-evidence/
Type: {driver_type}
"""
import os, sys, time, json

EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".verify-evidence"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def record_evidence(name, data):
    path = os.path.join(EVIDENCE_DIR, name)
    with open(path, "w", encoding="utf-8") as fh:
        if isinstance(data, (dict, list)):
            json.dump(data, fh, indent=2)
        else:
            fh.write(str(data))
    print(f"[evidence] Saved {{name}} -> {{path}}")

def main():
    print("Running runtime smoke verification...")
    # TODO: Perform observable runtime checks (e.g., HTTP probe, CLI execution, or Playwright browser)
    evidence = {{
        "timestamp": time.time(),
        "status": "unverified",
        "driver_type": "{driver_type}"
    }}
    record_evidence("smoke_run.json", evidence)
    print("Runtime smoke driver is a draft: implement observable assertions before verification.")
    return 2

if __name__ == "__main__":
    sys.exit(main())
'''
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print(f"Created smoke driver at {target} ({driver_type}).")
    print(f"Evidence directory ensured at {evidence_dir}.")
    print("Add this check to your VERIFY.md under the appropriate feature:")
    print("  - run: `python scripts/smoke_driver.py`")
    return 0


# ---- run ----------------------------------------------------------------------------------

def extract_failure_summary(output):
    """Find the core assertion or error line to provide fast, token-efficient diagnosis."""
    if not output:
        return None
    patterns = [
        re.compile(r"^\s*(?:AssertionError:?|assert\s+|FAIL:|Error:|Exception:?)\s*(.*)$", re.M),
        re.compile(r"^\s*E\s+(?:assert\s+|)(.*)$", re.M),
        re.compile(r"^\s*Expected:\s*(.*?)\s*Received:\s*(.*?)$", re.M),
        re.compile(r"^\s*---\s*FAIL:\s*(.*?)$", re.M),
        re.compile(r"^\s*panicked at\s*(.*)$", re.M),
    ]
    for pat in patterns:
        m = pat.search(output)
        if m:
            summary = m.group(0).strip()
            if len(summary) > 160:
                summary = summary[:157] + "..."
            return summary
    return None


def run_check(cmd, repo, timeout):
    """(ok, exit code or None, combined output, seconds)."""
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode == 0, p.returncode, (p.stdout or "") + (p.stderr or ""), time.time() - t0
    except subprocess.TimeoutExpired:
        return False, None, f"timed out after {timeout}s", time.time() - t0


def start_app(cmd, repo):
    """(process, log path). The app keeps running in the background; its output goes to a log.

    `exec` makes the shell replace itself with `cmd` instead of forking it as a child: on a
    shell where a single simple command is not tail-call-optimized away, `proc.pid` would
    otherwise name the shell, not the app, and killing+reaping `proc` would leave the real
    app process an orphaned zombie for `stop_app` to never actually confirm dead.
    """
    fd, log = tempfile.mkstemp(prefix="verify-app-", suffix=".log")
    posix = os.name != "nt"
    kw = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if not posix
          else {"start_new_session": True})
    run_cmd = f"exec {cmd}" if posix else cmd
    with os.fdopen(fd, "w") as fh:
        proc = subprocess.Popen(run_cmd, shell=True, cwd=repo, stdout=fh, stderr=subprocess.STDOUT, **kw)
    return proc, log


def stop_app(proc, stop_cmd, repo, timeout):
    if stop_cmd:
        run_check(stop_cmd, repo, timeout)
    if proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass


def wait_ready(cmd, proc, repo, timeout):
    """(ready, why not). Polls `ready` until it exits 0, the app dies, or the timeout passes."""
    if not cmd:
        time.sleep(1)
        return proc.poll() is None, f"the app exited with code {proc.poll()} before any check ran"
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return False, f"the app exited with code {proc.poll()} before it was ready"
        if run_check(cmd, repo, max(1, min(10, timeout)))[0]:
            return True, ""
        time.sleep(0.5)
    return False, f"'ready' did not pass within {timeout}s"


def tail_of(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().rstrip().splitlines()[-TAIL_LINES:]
    except OSError:
        return []


def cmd_run(repo, only, timeout, strict, budget=BUDGET, affected=None, stress=1, as_json=False, quarantine=False):
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        if as_json:
            print(json.dumps({"error": f"no {RECIPE} in {repo}", "exit": 2}))
        else:
            print(f"no {RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2
    features, blind = parse(read(repo, RECIPE), repo=repo)
    if not features:
        if as_json:
            print(json.dumps({"error": f"{RECIPE} has no '## <feature>' sections; nothing to run.", "exit": 2}))
        else:
            print(f"{RECIPE} has no '## <feature>' sections; nothing to run.")
        track(repo, [], only, budget, 1, strict)
        return 2

    if affected is not None:
        changed_files = get_affected_files(repo, affected if affected != "HEAD" else None)
        if not changed_files and affected == "HEAD":
            changed_files = get_affected_files(repo, "HEAD")
        if not changed_files:
            if as_json:
                print(json.dumps({
                    "verdict": "green", "detail": f"no files changed vs {affected}", "exit": 0,
                    "summary": {"features": 0, "passed": 0, "failed": 0}, "results": [],
                }, indent=2))
            else:
                print(f"AFFECTED: no changed files detected vs {affected}; all mapped features current.")
            return 0
        features = filter_affected(features, changed_files, repo)
        if not features:
            if as_json:
                print(json.dumps({
                    "verdict": "green", "detail": f"{len(changed_files)} changed file(s) touched no mapped features",
                    "exit": 0, "summary": {"features": 0, "passed": 0, "failed": 0}, "results": [],
                }, indent=2))
            else:
                print(f"AFFECTED: {len(changed_files)} changed file(s) touched no mapped features or oracles.")
            return 0
        if not as_json:
            print(f"AFFECTED: running {len(features)} feature(s) affected by {len(changed_files)} changed file(s).")

    try:
        check_hashes(repo)
    except (OSError, ValueError) as exc:
        if as_json:
            print(json.dumps({"error": f"Run: invalid oracle: {exc}", "exit": 1}))
        else:
            print(f"Run: invalid oracle: {exc}; no check was run.")
        track(repo, [], only, budget, 1, strict)
        return 1

    recipe = parse_run(read(repo, RECIPE))
    proc = log = None
    if recipe:
        for cmd in recipe["setup"]:
            ok, code, out, secs = run_check(cmd, repo, timeout)
            if not ok:
                if as_json:
                    print(json.dumps({"error": f"Run: setup failed ({cmd})", "exit": 1, "output": out[-1000:]}))
                else:
                    print(f"Run: setup failed ({cmd}); no check was run.")
                    for line in out.rstrip().splitlines()[-TAIL_LINES:]:
                        print(f"        {line}")
                track(repo, [], only, budget, 1, strict)
                return 1
        if recipe.get("login") and not as_json:
            print(f"Login: {recipe['login']}")
        if recipe.get("start"):
            t0 = time.time()
            proc, log = start_app(recipe["start"], repo)
            ready, why = wait_ready(recipe.get("ready"), proc, repo, timeout)
            if not ready:
                if as_json:
                    print(json.dumps({"error": f"Run: app not ready: {why}", "exit": 1}))
                else:
                    print(f"Run: app not ready: {why}; no check was run.")
                    for line in tail_of(log):
                        print(f"        {line}")
                stop_app(proc, recipe.get("stop"), repo, timeout)
                os.unlink(log)
                track(repo, [], only, budget, 1, strict)
                return 1
            if not as_json:
                print(f"Run: app ready in {time.time() - t0:.1f}s ({recipe['start']})")
    try:
        if recipe and recipe.get("doctor"):
            ok, _, out, _ = run_check(recipe["doctor"], repo, timeout)
            if not ok:
                if as_json:
                    print(json.dumps({"error": "Run: doctor failed", "exit": 1, "output": out[-1000:]}))
                else:
                    print("Run: doctor failed; no check was run.")
                    for line in out.rstrip().splitlines()[-TAIL_LINES:]:
                        print(f"        {line}")
                track(repo, [], only, budget, 1, strict)
                return 1
        return run_checks(repo, features, blind, recipe, only, timeout, strict, budget, stress, as_json, quarantine)
    finally:
        if proc:
            stop_app(proc, recipe.get("stop"), repo, timeout)
            try:
                os.unlink(log)
            except OSError:
                pass


def run_checks(repo, features, blind, recipe, only, timeout, strict, budget=BUDGET, stress=1, as_json=False, quarantine=False):
    results = []
    all_cmds = [c for f in features for _, c in f["checks"]]
    shown = [f for f in features if not only or only.lower() in f["name"].lower()]
    recipe_features, _ = parse(read(repo, RECIPE), repo=repo)
    known = {f["name"].lower() for f in (recipe_features or features) if not f["journey"]}
    passed = failed = unverified = unproven = journeys = broken = 0
    flaky_checks = []
    quarantined_hits = []
    state = load_state(repo)
    quarantined = set(state.get("quarantined", []))
    receipts = state.get("failures", {})
    missing_baseline = strict and not state.get("baseline")
    if missing_baseline and not as_json:
        print("  note  no baseline: freeze the finished checks before strict completion")
    signature = sha(json.dumps(check_hashes(repo), sort_keys=True))
    challenge = state.get("challenge", {})
    if challenge.get("verdict") == "caught" and challenge.get("check_signature") == signature:
        for key, row in challenge.get("mutated", {}).get("checks", {}).items():
            if key.startswith(challenge.get("feature", "") + "|") and not row.get("ok") and row.get("exit") is not None:
                receipts[key] = {"signature": signature, "exit": row["exit"], "output": row["output"]}
    for f in shown:
        if not as_json:
            print(("Journey: " if f["journey"] else "") + f["name"])
        if f["journey"]:
            journeys += 1
            if len(f["members"]) < 2:
                broken += 1
                if not as_json:
                    print("  BROKEN  a journey names fewer than two features: that is a feature, not a journey")
            for m in f["members"]:
                if m.lower() not in known:
                    broken += 1
                    if not as_json:
                        print(f"  BROKEN  journey names {m}: no such feature section in {RECIPE}")
        if not f["checks"]:
            unverified += 1
            if not as_json:
                print("  UNVERIFIED  no checks")
            continue
        for kind, cmd in f["checks"]:
            ok, code, out, secs = run_check(cmd, repo, timeout)
            check_passes = 1 if ok else 0
            if stress > 1:
                for _ in range(stress - 1):
                    s_ok, _, _, _ = run_check(cmd, repo, timeout)
                    if s_ok:
                        check_passes += 1
                if 0 < check_passes < stress:
                    flaky_checks.append((f["name"], kind, cmd, check_passes, stress))
                    quarantined.add(f"{f['name']}|{cmd}")
                    ok = False

            key = f"{f['name']}|{cmd}"
            is_quarantined = False
            if not ok and quarantine and (key in quarantined) and not strict:
                is_quarantined = True
                quarantined_hits.append((f["name"], kind, cmd))

            results.append((f["name"], kind, cmd, ok, out, code, is_quarantined))
            if is_quarantined:
                if not as_json:
                    print(f"  QUARANTINED  {kind}  {cmd}  [{secs:.1f}s] (flake isolated)")
            else:
                passed += ok
                failed += not ok
                if not as_json:
                    tag = "PASS" if ok else "FAIL"
                    extra = "" if ok else (" (timeout)" if code is None else f" (exit {code})")
                    print(f"  {tag}  {kind}  {cmd}  [{secs:.1f}s]{extra}")
                    if not ok:
                        cause = extract_failure_summary(out)
                        if cause:
                            print(f"        CAUSE  {cause}")
                        for line in out.rstrip().splitlines()[-TAIL_LINES:]:
                            print(f"        {line}")
        if not f["proofs"]:
            unproven += 1
            if not as_json:
                print("  note  no fail-proof recorded: nobody has shown these checks can go red")
        elif strict and not any(
                receipts.get(f"{f['name']}|{cmd}", {}).get("signature") == signature
                and f["signals"]
                and any(signal in receipts.get(f"{f['name']}|{cmd}", {}).get("output", "")
                        for signal in f["signals"])
                and not HARNESS_FAILURE.search(receipts.get(f"{f['name']}|{cmd}", {}).get("output", ""))
                for kind, cmd in f["checks"] if kind not in ("lint", "type", "types")):
            unproven += 1
            if not as_json:
                print("  note  no recorded failing run matching fail-signal for the current checks; fail-proof prose alone is not evidence")

    for fn, k, c, p_cnt, tot in flaky_checks:
        if not as_json:
            print(f"  FLAKY  {fn} ({k}): passed {p_cnt}/{tot} runs. Non-deterministic check detected.")
    if not recipe and any(k == "run" for f in features for k, _ in f["checks"]) and not as_json:
        print("note  'run' checks exist but there is no ## Run section: they assume the app is already up.")
    orphans = []
    if not only:
        orphans = [t for t in find_tests(repo) if not is_covered(t, all_cmds, repo)]
        if orphans and not as_json:
            print("Orphan tests (no feature's command names them):")
            for t in orphans:
                print(f"  {t}")
    if not as_json:
        if blind:
            print("Blind spots (a green run does not cover these):")
            for b in blind:
                print(f"  - {b}")
        else:
            print("Blind spots: none listed. A recipe that admits none has not looked.")

    incomplete = strict and (unverified or unproven or orphans or missing_baseline)
    try:
        changed_during_run = signature != sha(json.dumps(check_hashes(repo), sort_keys=True))
    except (OSError, ValueError):
        changed_during_run = True
    if changed_during_run and not as_json:
        print("CHECK CHANGED DURING RUN  repeat verification with stable checks and oracles")
    if quarantined:
        state["quarantined"] = sorted(quarantined)
        save_state(repo, state)
    norm_results = [(feat, kind, cmd, (ok or q), out, code) for feat, kind, cmd, ok, out, code, q in results]
    notes, bad = track(repo, norm_results, only, budget,
                       failed + broken + bool(incomplete) + changed_during_run + bool(flaky_checks), strict, signature)
    if not as_json:
        for n in notes:
            print(n)
        print(f"VERIFY: {len(shown) - journeys} features | {passed} checks pass, {failed} fail | "
              f"{unverified} unverified | {unproven} unproven | {len(orphans)} orphan tests | "
              f"{journeys} journeys, {broken} broken")
        if quarantined_hits:
            print(f"  QUARANTINED: {len(quarantined_hits)} check(s) isolated from failure.")
    red = bool(failed or broken or bad or incomplete or changed_during_run or flaky_checks)
    if as_json:
        report = {
            "verdict": "red" if red else "green",
            "strict": strict,
            "summary": {
                "features": len(shown) - journeys,
                "passed": passed,
                "failed": failed,
                "unverified": unverified,
                "unproven": unproven,
                "orphans": len(orphans),
                "journeys": journeys,
                "broken": broken,
                "flaky": len(flaky_checks),
                "quarantined": len(quarantined_hits),
            },
            "results": [
                {
                    "feature": feat, "kind": kind, "command": cmd, "ok": ok, "exit": code,
                    "cause": None if ok else extract_failure_summary(out),
                    "quarantined": q,
                }
                for feat, kind, cmd, ok, out, code, q in results
            ],
            "blind_spots": blind,
            "exit": 1 if red else 0,
        }
        print(json.dumps(report, indent=2))
        return report["exit"]
    if red:
        return 1
    return 0


# ---- loop memory --------------------------------------------------------------------------
# One run has no memory. STATE remembers across runs, so the loop can see what a single run
# cannot: the same failure twice, a fix that broke something else, a check edited to pass, and
# whether the last run is still true of the files on disk.

def sha(text):
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16]


def load_state(repo):
    try:
        with open(os.path.join(repo, STATE), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(repo, state):
    with open(os.path.join(repo, STATE), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(state, fh, indent=1, sort_keys=True)


def tree_sig(repo):
    """Content signature outside SKIP_DIRS; preserved timestamps cannot hide an edit."""
    h = hashlib.sha256()
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f == STATE or f.endswith(".pyc"):
                continue
            p = os.path.join(root, f)
            try:
                h.update(os.path.relpath(p, repo).encode("utf-8", "replace") + b"\0")
                with open(p, "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        h.update(chunk)
                h.update(b"\0")
            except OSError:
                continue
    return h.hexdigest()[:16]


def check_hashes(repo):
    """What the agent must not edit to get a pass: the test files, and the check commands in VERIFY.md."""
    hashes = {t: sha(read(repo, t)) for t in find_tests(repo)}
    recipe_text = read(repo, RECIPE)
    features, _ = parse(recipe_text, repo=repo)
    for inc in find_includes(recipe_text):
        inc_norm = os.path.normpath(inc).replace("\\", "/")
        if os.path.isfile(os.path.join(repo, inc)):
            hashes[inc_norm] = sha(read(repo, inc))
    for f in features:
        # Direct script paths are frozen automatically; imported helpers and data
        # still require explicit oracle entries. Do not parse inline program strings.
        scripts = []
        for _, cmd in f["checks"]:
            if re.search(r"(?:^|\s)-c(?:\s|$)", cmd):
                continue
            tokens = re.findall(r'"[^"\n]*"|\'[^\'\n]*\'|[^\s]+', cmd)
            scripts.extend(token.strip("\"'") for token in tokens
                           if token.strip("\"'").lower().endswith((".py", ".js", ".mjs", ".cjs", ".sh", ".ps1")))
        for name in f["oracles"] + [p for p in scripts if os.path.isfile(os.path.join(repo, p))]:
            path = os.path.realpath(os.path.join(repo, name))
            if os.path.commonpath([os.path.realpath(repo), path]) != os.path.realpath(repo):
                raise ValueError(f"oracle must be inside the repo: {name}")
            with open(path, "rb") as fh:
                hashes[name] = hashlib.sha256(fh.read()).hexdigest()[:16]
    hashes[RECIPE + " checks"] = sha("\n".join(f"{f['name']}|{k}|{c}" for f in features for k, c in f["checks"]))
    hashes[RECIPE + " signals"] = sha(json.dumps([(f["name"], f["signals"]) for f in features]))
    hashes[RECIPE + " run"] = sha(json.dumps(parse_run(read(repo, RECIPE)), sort_keys=True))
    return hashes


def tampered(repo, state):
    base = state.get("baseline") or {}
    if not base:
        return []
    cur = check_hashes(repo)
    return sorted(k for k in base if cur.get(k) != base[k])


HARNESS_FAILURE = re.compile(r"ModuleNotFoundError|ImportError|FileNotFoundError|SyntaxError|missing dependency|command not found|not recognized as|can\'t open file", re.I)


NOISE = re.compile(r"\S*[\\/](?:tmp|temp)[\\/]\S*|/tmp/\S+|0x[0-9a-f]+|\d+(?:\.\d+)?s\b|\d{2}:\d{2}:\d{2}", re.I)


def fingerprint(cmd, out):
    """The failure with its noise (timings, temp paths, addresses) removed, so 'the same' is comparable."""
    tail = "\n".join(out.rstrip().splitlines()[-TAIL_LINES:])
    return sha(cmd + "\0" + NOISE.sub("", tail))


def track(repo, results, only, budget, failures, strict=False, signature=None):
    """Compare this run to the last one and save it. (lines to print, True if the run must fail)."""
    if only:
        return ["note  --only run: loop state not updated (only a whole run can be compared)"], False
    state = load_state(repo)
    prev, checks, lines = state.get("checks", {}), {}, []
    receipts = state.setdefault("failures", {})
    if results and signature is None:
        signature = sha(json.dumps(check_hashes(repo), sort_keys=True))
    for feat, kind, cmd, ok, out, code in results:
        key = f"{feat}|{cmd}"
        p = prev.get(key, {})
        fp = None if ok else fingerprint(cmd, out)
        count = (p.get("count", 0) + 1) if (not ok and p.get("fp") == fp) else (0 if ok else 1)
        checks[key] = {"ok": ok, "fp": fp, "count": count, "exit": code, "output": out[-4000:]}
        if not ok and code is not None and out.strip():
            receipts[key] = {"signature": signature, "exit": code, "output": out[-4000:]}
        if p.get("ok") and not ok:
            lines.append(f"NEWLY RED  {feat} ({kind}): it passed last run, so the last change broke it")
        elif p and not p.get("ok") and ok:
            lines.append(f"NEWLY GREEN  {feat} ({kind})")
        if count >= 2:
            lines.append(f"SAME FAILURE x{count}  {feat} ({kind}): the same output again. Your picture of the "
                         "system is wrong; re-read the code and this output before another try")
    keep = (state.get("scope") or {}).get("keep", [])
    broke = [k for k in keep if k in checks and not checks[k]["ok"]]
    for k in broke:
        lines.append(f"KEEP-GREEN BROKEN  {k.split('|')[0]}: it passed when this fix began. "
                     "Undo what broke it before going on")
    strays = out_of_scope(repo, state)
    for r in strays:
        lines.append(f"OUT OF SCOPE  {r} changed, and the fix was not allowed to touch it. Revert it, or "
                     "widen the scope on purpose with `verify.py scope --add` and say why")
    try:
        changed = tampered(repo, state)
    except (OSError, ValueError) as exc:
        changed = [str(exc)]
    for c in changed:
        lines.append(f"CHECK CHANGED  {c} differs from the baseline. Loosening a check is not a fix: "
                     "restore it, or have a person review it and run `verify.py baseline`")
    red = bool(failures or changed or strays)
    rounds = state.get("rounds", 0) + 1 if red else 0
    if red and rounds >= budget:
        lines.append(f"BUDGET  {rounds} red runs in a row (budget {budget}): stop, report what passes, "
                     "what fails and what you would try next")
    state.update({"checks": checks, "rounds": rounds, "result": "red" if red else "green",
                  "strict": strict, "tree": tree_sig(repo)})
    save_state(repo, state)
    return lines, bool(changed or strays)


def file_sigs(repo):
    """{relative path: content hash} for every file outside SKIP_DIRS: what `scope` compares against."""
    sigs = {}
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f == STATE or f.endswith(".pyc"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, repo).replace(os.sep, "/")
            try:
                if os.path.getsize(p) > 5_000_000:
                    sigs[rel] = f"big:{os.path.getsize(p)}"
                    continue
                with open(p, "rb") as fh:
                    sigs[rel] = hashlib.sha256(fh.read()).hexdigest()[:16]
            except OSError:
                continue
    return sigs


def in_scope(rel, allow):
    return any(fnmatch.fnmatch(rel, a) or rel.startswith(a.rstrip("/") + "/") for a in allow)


def out_of_scope(repo, state):
    """Files changed, added or removed since `scope` was declared that the fix was not allowed to touch."""
    sc = state.get("scope")
    if not sc:
        return []
    now, snap = file_sigs(repo), sc.get("snap", {})
    moved = [r for r in set(now) | set(snap) if now.get(r) != snap.get(r)]
    return sorted(r for r in moved if not in_scope(r, sc.get("allow", [])))


def cmd_scope(repo, patterns, add, clear, check):
    state = load_state(repo)
    sc = state.get("scope")
    if clear:
        state.pop("scope", None)
        save_state(repo, state)
        print("scope cleared.")
        return 0
    if check or (not patterns and sc):
        if not sc:
            print("no scope declared.")
            return 0
        bad = out_of_scope(repo, state)
        print(f"scope: {', '.join(sc['allow'])} ({len(sc.get('keep', []))} passing check(s) on watch)")
        for r in bad:
            print(f"  OUT OF SCOPE  {r}")
        return 1 if bad else 0
    if not patterns:
        print("scope needs the paths the fix may touch, e.g. `verify.py scope src/cart.py tests/test_cart.py`.")
        return 2
    if add:
        if not sc:
            print("no scope to widen; declare one first (`verify.py scope PATH...`).")
            return 2
        sc["allow"] = sorted(set(sc["allow"]) | set(patterns))
        save_state(repo, state)
        print(f"scope widened: {', '.join(sc['allow'])}. Say why in your report.")
        return 0
    keep = sorted(k for k, v in state.get("checks", {}).items() if v.get("ok"))
    state["scope"] = {"allow": sorted(set(patterns)), "snap": file_sigs(repo), "keep": keep}
    save_state(repo, state)
    print(f"scope set: {', '.join(state['scope']['allow'])}. Edits outside it fail the run.")
    if keep:
        print(f"keep-green: {len(keep)} check(s) passed on the last run and must still pass when you are done.")
    else:
        print("note  no passing run on record: run `verify.py run` first, or nothing is on watch "
              "and you cannot tell what you broke.")
    return 0


def cmd_baseline(repo):
    if not os.path.isfile(os.path.join(repo, RECIPE)):
        print(f"no {RECIPE} in {repo}. Run `verify.py init` first.")
        return 2
    state = load_state(repo)
    try:
        state["baseline"] = check_hashes(repo)
    except (OSError, ValueError) as exc:
        print(f"invalid oracle: {exc}")
        return 2
    save_state(repo, state)
    print(f"baseline recorded: {len(state['baseline'])} check file(s). From here an edit to any of "
          "them fails the run until a person re-baselines.")
    return 0


def status_verdict(repo):
    """(state, detail, exit). Single decision path for text and --json output."""
    if not os.path.isfile(os.path.join(repo, RECIPE)):
        return "none", "no VERIFY.md; this repo does not use verify-loop", 0
    state = load_state(repo)
    if not state.get("result"):
        return "never-run", "VERIFY.md exists, no run recorded", 3
    try:
        changed = tampered(repo, state)
    except (OSError, ValueError) as exc:
        return "tampered", str(exc), 1
    if changed:
        return "tampered", f"{', '.join(changed)} differs from the baseline", 1
    strays = out_of_scope(repo, state)
    if strays:
        return ("out-of-scope", f"{', '.join(strays[:3])}{' ...' if len(strays) > 3 else ''} "
                "changed outside the declared scope", 1)
    if state["result"] != "green":
        return "red", f"red run {state.get('rounds', 0)} in a row", 1
    if state.get("tree") != tree_sig(repo):
        return "stale", "files changed since the last green run", 3
    if not state.get("strict"):
        return "partial", "last run was not strict; run --strict before claiming done", 3
    return "green", "", 0


def cmd_status(repo, as_json=False):
    """One line for a hook or a human: is the last run green and still true of the files? Exit 0 yes,
    1 red, 3 stale or never run. No VERIFY.md means this repo does not use it: 0, silent.
    --json prints one object with the same verdict plus failing checks and the last challenge."""
    name, detail, code = status_verdict(repo)
    if as_json:
        state = load_state(repo) if name != "none" else {}
        checks = state.get("checks", {}) or {}
        challenge = state.get("challenge") or {}
        print(json.dumps({
            "state": name, "detail": detail, "exit": code,
            "strict": bool(state.get("strict")), "rounds": state.get("rounds", 0),
            "failing": sorted(k for k, r in checks.items() if isinstance(r, dict) and not r.get("ok")),
            "checks": len(checks), "receipts": sorted((state.get("failures") or {}).keys()),
            "challenge": {"feature": challenge.get("feature"), "verdict": challenge.get("verdict")}
            if challenge else None,
        }, indent=2))
        return code
    if name == "none":
        return 0
    print(f"VERIFY-STATE: {name}" + (f" ({detail})" if detail else ""))
    return code


def diagnose_failure(out, exit_code, check_name, state=None):
    """Diagnose a failure into ('harness-gap' | 'spec-drift' | 'product-gap', summary, recommended_action)."""
    if state and state.get("result") == "tampered":
        return ("spec-drift", "Baseline tampering detected (check commands or oracle files modified).",
                "Consult team or spec. If intentional, run `verify.py baseline`.")
    if state and "CHECK CHANGED" in str(state.get("detail", "")):
        return ("spec-drift", "Test checks or oracle files differ from the baseline.",
                "Do NOT weaken check silently. Confirm changes and re-run `verify.py baseline`.")

    out_lower = (out or "").lower()
    if re.search(r"eaddrinuse|address already in use|port \d+ is already in use|bind: address already in use", out_lower):
        return ("harness-gap", "Port collision: target port is already in use by another process.",
                "Kill conflicting process or adjust port in ## Run. Do NOT edit product logic.")
    if re.search(r"econnrefused|connection refused|actively refused|failed to connect", out_lower):
        return ("harness-gap", "Connection refused: service or database is not reachable.",
                "Ensure service is running. Fix ## Run recipe or start scripts.")
    if "timed out after" in out_lower or exit_code is None:
        return ("harness-gap", "Execution timeout: command or readiness probe timed out.",
                "Increase timeout using --timeout or fix slow initialization / hang in ## Run scripts.")
    if HARNESS_FAILURE.search(out or ""):
        m = HARNESS_FAILURE.search(out or "")
        return ("harness-gap", f"Environment / dependency error: {m.group(0)}.",
                "Install missing packages, check virtualenv, or fix script invocation. Do NOT modify product logic.")

    cause = extract_failure_summary(out) or "Test assertion or contract failed"
    return ("product-gap", f"Product defect: {cause}",
            "Pin touched files with `verify.py scope <files>` and fix product logic in minimal slices.")


def cmd_triage(repo, as_json=False):
    """Diagnose the latest verification failure into harness-gap, spec-drift, or product-gap."""
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        if as_json:
            print(json.dumps({"error": f"no {RECIPE} in {repo}", "exit": 2}))
        else:
            print(f"no {RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2

    state = load_state(repo)
    if not state or "result" not in state:
        if as_json:
            print(json.dumps({"error": "no verification run recorded; run verify.py run first", "exit": 2}))
        else:
            print("No verification run recorded in .verify-state.json. Run `verify.py run` first.")
        return 2

    if state.get("result") == "green":
        if as_json:
            print(json.dumps({
                "verdict": "green",
                "category": None,
                "summary": "Last verification run was GREEN. No failures to triage.",
                "action": "Proceed to deployment, commit, or next task slice.",
                "exit": 0,
            }, indent=2))
        else:
            print("TRIAGE: Last verification run was GREEN. No failures to triage.")
        return 0

    checks = state.get("checks", {})
    failing_entries = [(k, v) for k, v in checks.items() if isinstance(v, dict) and not v.get("ok")]

    try:
        changed = tampered(repo, state)
    except (OSError, ValueError) as exc:
        changed = [str(exc)]

    if changed:
        category, summary, action = ("spec-drift", f"Baseline mismatch: {', '.join(changed)} changed.",
                                     "Confirm changes with team/spec. If intentional, run `verify.py baseline`.")
        target_check = "baseline"
    elif failing_entries:
        target_check, check_data = failing_entries[0]
        out = check_data.get("output", "")
        exit_code = check_data.get("exit")
        category, summary, action = diagnose_failure(out, exit_code, target_check, state)
    else:
        strays = out_of_scope(repo, state)
        if strays:
            category, summary, action = ("spec-drift", f"Out of scope edits in: {', '.join(strays)}",
                                         "Revert files outside scope or widen with `verify.py scope --add <path>`.")
            target_check = "scope"
        else:
            category, summary, action = ("product-gap", "Verification failed.",
                                         "Inspect logs and run `verify.py run`.")
            target_check = "unknown"

    if as_json:
        report = {
            "verdict": "fail",
            "category": category,
            "failing_check": target_check,
            "summary": summary,
            "action": action,
            "total_failing": len(failing_entries),
            "exit": 0,
        }
        print(json.dumps(report, indent=2))
    else:
        print(f"TRIAGE: [{category.upper()}] on {target_check}")
        print(f"  Summary: {summary}")
        print(f"  Action:  {action}")
    return 0


def cmd_scaffold_oracle(repo, spec_path, oracle_type="auto"):
    """Scaffold a verification oracle and check script from OpenAPI or JSON Schema."""
    full_path = spec_path if os.path.isabs(spec_path) else os.path.join(repo, spec_path)
    if not os.path.isfile(full_path):
        print(f"SCAFFOLD-ORACLE: file not found: {spec_path}")
        return 2

    rel_spec = os.path.relpath(full_path, repo).replace("\\", "/")
    content = ""
    try:
        with open(full_path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError as exc:
        print(f"SCAFFOLD-ORACLE: cannot read {spec_path}: {exc}")
        return 2

    spec_data = None
    if full_path.endswith(".json"):
        try:
            spec_data = json.loads(content)
        except ValueError:
            pass
    elif full_path.endswith((".yaml", ".yml")):
        try:
            import yaml
            spec_data = yaml.safe_load(content)
        except Exception:
            pass

    is_openapi = False
    is_schema = False
    if oracle_type == "openapi" or (oracle_type == "auto" and (
            (isinstance(spec_data, dict) and ("openapi" in spec_data or "swagger" in spec_data or "paths" in spec_data))
            or "openapi:" in content or "swagger:" in content or "paths:" in content)):
        is_openapi = True
    elif oracle_type == "schema" or (oracle_type == "auto" and (
            (isinstance(spec_data, dict) and ("$schema" in spec_data or "properties" in spec_data))
            or "$schema" in content or "properties:" in content)):
        is_schema = True

    scripts_dir = os.path.join(repo, "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    evidence_dir = os.path.join(repo, ".verify-evidence")
    os.makedirs(evidence_dir, exist_ok=True)

    if is_openapi:
        target_script = os.path.join(scripts_dir, "smoke_api.py")
        endpoints = []
        if isinstance(spec_data, dict) and "paths" in spec_data:
            for p, methods in spec_data["paths"].items():
                if isinstance(methods, dict):
                    for m in methods:
                        if m.lower() in ("get", "post", "put", "delete", "patch"):
                            endpoints.append((m.upper(), p))
        if not endpoints:
            for m in re.finditer(r"^\s*(/[A-Za-z0-9_/{}.-]+):\s*$", content, re.M):
                endpoints.append(("GET", m.group(1)))
        if not endpoints:
            endpoints = [("GET", "/health"), ("GET", "/api/v1/status")]

        first_ep = endpoints[0][1] if endpoints else "/health"
        script_code = f'''#!/usr/bin/env python3
"""smoke_api.py — Generated API contract verification probe.
Oracle: {rel_spec}
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".verify-evidence"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)

ENDPOINTS = {json.dumps(endpoints[:10], indent=2)}

def test_endpoint(base_url, method, path):
    url = base_url.rstrip("/") + path
    req = urllib.request.Request(url, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = time.time() - t0
            print(f"[{{resp.status}} OK] {{method}} {{path}} ({{elapsed:.2f}}s)")
            return True, resp.status, None
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        print(f"[{{e.code}} ERR] {{method}} {{path}} ({{elapsed:.2f}}s): {{e.reason}}")
        return False, e.code, str(e.reason)
    except Exception as exc:
        print(f"[FAIL] {{method}} {{path}}: {{exc}}")
        return False, 0, str(exc)

def main():
    parser = argparse.ArgumentParser(description="API contract smoke check")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--endpoint", default=None)
    args = parser.parse_args()

    targets = [ep for ep in ENDPOINTS if not args.endpoint or ep[1] == args.endpoint]
    if not targets and args.endpoint:
        targets = [("GET", args.endpoint)]

    all_ok = True
    results = []
    for method, path in targets:
        ok, code, err = test_endpoint(args.base_url, method, path)
        results.append({{"method": method, "path": path, "ok": ok, "status": code, "error": err}})
        if not ok:
            all_ok = False

    evidence = {{"timestamp": time.time(), "oracle": "{rel_spec}", "results": results}}
    with open(os.path.join(EVIDENCE_DIR, "api_contract_evidence.json"), "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
'''
        with open(target_script, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(script_code)

        print(f"SCAFFOLD-ORACLE: Generated API contract runner at scripts/smoke_api.py")
        print(f"Discovered {len(endpoints)} endpoint(s) from {rel_spec}.")
        print("Suggested addition to VERIFY.md:")
        print(f"  ## API Contract: {first_ep}")
        print(f"  - run: `python scripts/smoke_api.py --endpoint {first_ep}`")
        print(f"  - oracle: {rel_spec}")
        print(f"  - fail-signal: [FAIL] or [ERR]")
        print(f"  - fail-proof: simulated endpoint failure, check rejected, restored")
        return 0

    elif is_schema:
        target_script = os.path.join(scripts_dir, "validate_schema.py")
        script_code = f'''#!/usr/bin/env python3
"""validate_schema.py — Schema conformance validator.
Oracle: {rel_spec}
"""
import json, os, sys

SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "{rel_spec}"))

def validate(payload):
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    req = schema.get("required", [])
    for field in req:
        if field not in payload:
            raise ValueError(f"SchemaValidationError: missing required field '{{field}}'")
    return True

def main():
    test_payload = sys.argv[1] if len(sys.argv) > 1 else None
    if not test_payload:
        print("Usage: python scripts/validate_schema.py <payload.json>")
        return 2
    with open(test_payload, encoding="utf-8") as fh:
        data = json.load(fh)
    try:
        validate(data)
        print("Schema validation passed.")
        return 0
    except ValueError as e:
        print(f"SchemaValidationError: {{e}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        with open(target_script, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(script_code)

        print(f"SCAFFOLD-ORACLE: Generated schema validator at scripts/validate_schema.py")
        print("Suggested addition to VERIFY.md:")
        print(f"  ## Schema Validation")
        print(f"  - test: `python scripts/validate_schema.py data.json`")
        print(f"  - oracle: {rel_spec}")
        print(f"  - fail-signal: SchemaValidationError")
        print(f"  - fail-proof: removed required field in scratch test, check rejected, restored")
        return 0
    else:
        print(f"SCAFFOLD-ORACLE: unrecognized specification format in {spec_path}. Specify --type openapi or --type schema.")
        return 2


def cmd_watch(repo, interval=2.0, max_runs=0):
    """Continuously poll repo for file changes and run affected checks."""
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        print(f"no {RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2
    print(f"Watching {repo} for changes (interval: {interval}s)... Press Ctrl+C to stop.")
    last_sig = tree_sig(repo)
    runs_done = 0
    try:
        while True:
            time.sleep(interval)
            cur_sig = tree_sig(repo)
            if cur_sig != last_sig:
                last_sig = cur_sig
                t_str = time.strftime("%H:%M:%S")
                print(f"\n[WATCH {t_str}] Change detected. Running affected checks...")
                code = cmd_run(repo, only=None, timeout=120, strict=False, budget=BUDGET, affected="HEAD")
                runs_done += 1
                if max_runs and runs_done >= max_runs:
                    print(f"[WATCH] Reached max-runs ({max_runs}). Stopping watcher.")
                    return code
    except KeyboardInterrupt:
        print("\n[WATCH] Stopped.")
        return 0


def main():
    utf8_streams()
    ap = argparse.ArgumentParser(description="Feature-to-check map: draft VERIFY.md, run it.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init", help="draft VERIFY.md from the test files on disk")
    i.add_argument("repo", nargs="?", default=".")
    r = sub.add_parser("run", help="run every check in VERIFY.md")
    r.add_argument("repo", nargs="?", default=".")
    r.add_argument("--only", help="run only features whose name contains this text")
    r.add_argument("--timeout", type=int, default=120, help="seconds per check (default 120)")
    r.add_argument("--strict", action="store_true",
                   help="require recorded failure evidence and reject unverified features or orphan tests")
    r.add_argument("--budget", type=int, default=BUDGET,
                   help="red runs in a row before the run says stop (default 5)")
    r.add_argument("--affected", nargs="?", const="HEAD", default=None,
                   help="run only features affected by changes against git ref (default: HEAD)")
    r.add_argument("--stress", type=int, default=1,
                   help="run checks N times to detect non-deterministic / flaky checks (default: 1)")
    r.add_argument("--quarantine", action="store_true",
                   help="quarantine non-deterministic flaky checks from failing the run")
    r.add_argument("--json", action="store_true",
                   help="output run results and summary as JSON")
    b = sub.add_parser("baseline", help="freeze the check files; later edits to them fail the run")
    b.add_argument("repo", nargs="?", default=".")
    t = sub.add_parser("status", help="is the last run green and still true of the files? (exit 0/1/3)")
    t.add_argument("repo", nargs="?", default=".")
    t.add_argument("--json", action="store_true", help="print one JSON object (same exit codes)")
    tr = sub.add_parser("triage", help="diagnose latest failure into harness-gap, spec-drift, or product-gap")
    tr.add_argument("repo", nargs="?", default=".")
    tr.add_argument("--json", action="store_true", help="output triage report as JSON")
    m = sub.add_parser("tests", help="map every test function to a feature; flag tests that cannot fail")
    m.add_argument("repo", nargs="?", default=".")
    m.add_argument("--strict", action="store_true",
                   help="exit 1 on hollow, unmapped, skipped or unparseable Python tests")
    c = sub.add_parser("scope", help="name the files a fix may touch; edits outside them fail the run")
    c.add_argument("patterns", nargs="*", help="files, folders or globs the fix may touch")
    c.add_argument("--repo", default=".")
    c.add_argument("--add", action="store_true", help="widen the existing scope")
    c.add_argument("--clear", action="store_true", help="drop the scope")
    c.add_argument("--check", action="store_true", help="list edits outside the scope (exit 1 if any)")
    sd = sub.add_parser("scaffold-driver", help="generate runtime smoke driver and evidence directory")
    sd.add_argument("repo", nargs="?", default=".")
    sd.add_argument("--type", choices=["web", "api", "cli", "auto"], default="auto",
                    help="type of driver to scaffold (default: auto)")
    so = sub.add_parser("scaffold-oracle", help="generate test driver and VERIFY.md feature from OpenAPI spec or JSON schema")
    so.add_argument("spec", help="path to OpenAPI (yaml/json) or JSON Schema file")
    so.add_argument("repo", nargs="?", default=".")
    so.add_argument("--type", choices=["auto", "openapi", "schema"], default="auto", help="specification type")
    w = sub.add_parser("watch", help="watch repo for changes and run affected checks continuously")
    w.add_argument("repo", nargs="?", default=".")
    w.add_argument("--interval", type=float, default=2.0, help="polling interval in seconds (default: 2.0)")
    w.add_argument("--max-runs", type=int, default=0, help="exit after N runs (default: 0 = run forever)")
    ch = sub.add_parser("challenge", help="challenge a feature check with one explicit mutation in scratch copies")
    ch.add_argument("repo", nargs="?", default=".")
    ch.add_argument("--feature", required=True, help="exact feature name in VERIFY.md")
    ch.add_argument("--mutation", help="JSON file with file, before, after and claim")
    ch.add_argument("--auto", metavar="FILE",
                    help="generate standard mutations for this product file; report a mutation score")
    ch.add_argument("--max", type=int, default=20, help="most mutations to try with --auto (default 20)")
    ch.add_argument("--json", action="store_true", help="with --auto, print the score as JSON")
    ch.add_argument("--timeout", type=int, default=120, help="seconds per check")
    ci = sub.add_parser("ci", help="fresh proof from committed inputs; ignore local verification state")
    ci.add_argument("repo", nargs="?", default=".")
    ci.add_argument("--plan", required=True, help="committed repo-relative JSON feature/mutation list")
    ci.add_argument("--output", required=True, help="evidence directory outside the checkout")
    ci.add_argument("--timeout", type=int, default=120, help="seconds per check")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    if a.cmd == "ci":
        from ci import cmd_ci
        sys.exit(cmd_ci(sys.modules[__name__], repo, a.plan, a.output, a.timeout))
    if a.cmd == "challenge":
        if bool(a.mutation) == bool(a.auto):
            ap.error("challenge needs exactly one of --mutation or --auto")
        if a.auto:
            from mutate import cmd_auto
            sys.exit(cmd_auto(sys.modules[__name__], repo, a.feature, a.auto, a.timeout, a.max, a.json))
        from challenge import cmd_challenge
        sys.exit(cmd_challenge(sys.modules[__name__], repo, a.feature, a.mutation, a.timeout))
    if a.cmd == "scaffold-driver":
        sys.exit(cmd_scaffold_driver(repo, a.type))
    if a.cmd == "scaffold-oracle":
        sys.exit(cmd_scaffold_oracle(repo, a.spec, a.type))
    if a.cmd == "watch":
        sys.exit(cmd_watch(repo, a.interval, a.max_runs))
    if a.cmd == "scope":
        sys.exit(cmd_scope(repo, a.patterns, a.add, a.clear, a.check))
    if a.cmd == "init":
        sys.exit(cmd_init(repo))
    if a.cmd == "baseline":
        sys.exit(cmd_baseline(repo))
    if a.cmd == "status":
        sys.exit(cmd_status(repo, a.json))
    if a.cmd == "triage":
        sys.exit(cmd_triage(repo, a.json))
    if a.cmd == "tests":
        sys.exit(cmd_tests(repo, a.strict))
    sys.exit(cmd_run(repo, a.only, a.timeout, a.strict, a.budget, a.affected, a.stress, a.json, a.quarantine))


if __name__ == "__main__":
    main()
