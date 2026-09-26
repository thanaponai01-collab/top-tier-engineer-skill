#!/usr/bin/env python3
"""verify.py — the feature-to-check map behind verify-loop.

VERIFY.md at the repo root maps each feature to the commands that prove it. Two commands:

  init   Draft VERIFY.md from the test files already on disk, one feature per test file
         (or per feature folder). A draft: the agent fixes the grouping and adds the
         real-run checks. Never overwrites an existing VERIFY.md.
  run    Run every check, print a result per feature, and say what a green run does NOT
         cover: features with no check, checks nobody proved can fail, test files that
         belong to no feature, and the blind spots the recipe lists.

A check passes when its command exits 0. Commands run through the shell, like a Makefile:
only run a VERIFY.md from a repo you trust. Stdlib only.

VERIFY.md format:

  ## Feature name
  - test: `python -m pytest tests/test_x.py -q`
  - run: `python app.py --smoke`
  - fail-proof: broke the tax rounding, test_x went red, reverted

  ## Blind spots
  - the payment gateway is stubbed

Usage:
  python scripts/verify.py init [repo]
  python scripts/verify.py run  [repo] [--only TEXT] [--timeout 120] [--strict]

Exit: run 0 = no check failed; 1 = a check failed (or --strict and something is unverified or
unproven); 2 = no usable VERIFY.md. Summary line:
  VERIFY: <f> features | <p> checks pass, <x> fail | <u> unverified | <n> unproven | <o> orphan tests
"""
import argparse, os, re, subprocess, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams

RECIPE = "VERIFY.md"
GENERIC_DIRS = {"tests", "test", "__tests__", "spec", "specs", "e2e", "integration", "unit"}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target",
             "vendor", ".tox", "fixture", "fixtures"}
TEST_PY = re.compile(r"^(test_.+|.+_test)\.py$")
TEST_JS = re.compile(r"^.+\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$")
TAIL_LINES = 12


# ---- reading the recipe -------------------------------------------------------------------

def parse(text):
    """(features, blind_spots). A feature is {name, checks: [(kind, command)], proofs: [str]}."""
    features, blind, cur, in_blind = [], [], None, False
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            if h.group(1).lower() == "blind spots":
                cur, in_blind = None, True
            else:
                cur = {"name": h.group(1), "checks": [], "proofs": []}
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
        elif val:
            cur["checks"].append((kind, val))
    return features, blind


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
        "for each feature, and replace every TODO.",
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


# ---- run ----------------------------------------------------------------------------------

def run_check(cmd, repo, timeout):
    """(ok, exit code or None, combined output, seconds)."""
    t0 = time.time()
    try:
        p = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode == 0, p.returncode, (p.stdout or "") + (p.stderr or ""), time.time() - t0
    except subprocess.TimeoutExpired:
        return False, None, f"timed out after {timeout}s", time.time() - t0


def cmd_run(repo, only, timeout, strict):
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        print(f"no {RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2
    features, blind = parse(read(repo, RECIPE))
    if not features:
        print(f"{RECIPE} has no '## <feature>' sections; nothing to run.")
        return 2

    all_cmds = [c for f in features for _, c in f["checks"]]
    shown = [f for f in features if not only or only.lower() in f["name"].lower()]
    passed = failed = unverified = unproven = 0
    for f in shown:
        print(f["name"])
        if not f["checks"]:
            unverified += 1
            print("  UNVERIFIED  no checks")
            continue
        for kind, cmd in f["checks"]:
            ok, code, out, secs = run_check(cmd, repo, timeout)
            passed += ok
            failed += not ok
            tag = "PASS" if ok else "FAIL"
            extra = "" if ok else (" (timeout)" if code is None else f" (exit {code})")
            print(f"  {tag}  {kind}  {cmd}  [{secs:.1f}s]{extra}")
            if not ok:
                for line in out.rstrip().splitlines()[-TAIL_LINES:]:
                    print(f"        {line}")
        if not f["proofs"]:
            unproven += 1
            print("  note  no fail-proof recorded: nobody has shown these checks can go red")

    orphans = []
    if not only:
        orphans = [t for t in find_tests(repo) if not is_covered(t, all_cmds, repo)]
        if orphans:
            print("Orphan tests (no feature's command names them):")
            for t in orphans:
                print(f"  {t}")
    if blind:
        print("Blind spots (a green run does not cover these):")
        for b in blind:
            print(f"  - {b}")
    else:
        print("Blind spots: none listed. A recipe that admits none has not looked.")

    print(f"VERIFY: {len(shown)} features | {passed} checks pass, {failed} fail | "
          f"{unverified} unverified | {unproven} unproven | {len(orphans)} orphan tests")
    if failed or (strict and (unverified or unproven)):
        return 1
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
                   help="also exit 1 when a feature is unverified or has no fail-proof")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    if a.cmd == "init":
        sys.exit(cmd_init(repo))
    sys.exit(cmd_run(repo, a.only, a.timeout, a.strict))


if __name__ == "__main__":
    main()
