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
         Re-freezing a changed or removed check needs --reviewed-by and --reason; the
         re-baseline is recorded and shown by status and report until it is committed.
  status Was the last whole run strict, green and current? One line, exit 0/1/3.
  report The caller answer: verdict, VERIFY: line, observed rejections, passes and gaps.
  scaffold-skill / skill-check  Create mode: draft and lint a project-local `verify` skill.
  maintain  Maintain mode: what the next pass over that skill must map, re-prove, fix or re-drive.
  scope  Before a fix, name the files it may touch. Any later edit outside them fails the run
         (OUT OF SCOPE), and every check that passed when the fix began stays on watch.

`run` also remembers itself in .verify-state.json (gitignore .verify-state*; VERIFY_AGENT=<name>
gives each agent its own loop memory while the baseline and receipts stay shared; --assess,
--state-dir DIR or VERIFY_STATE_DIR keep that memory and the caches outside the repo, so assessing
a repo leaves its tree untouched): it says NEWLY RED when a fix
broke something that passed, SAME FAILURE when a check fails identically twice, and BUDGET after
--budget red runs in a row. A `--only` run compares nothing and saves nothing.
Strict runs require retained failure output for the current checks plus a fail-proof note;
a non-strict pass is partial, never a successful completion status. A top-level
`require: challenge` line also makes strict demand a caught `challenge` mutation. The state file is
sealed with a content hash: a hand-edited one reads as tampered until it is deleted.

A pass already proved for the same command on the same content (by any agent, in any worktree of
the repo) is reused and shown as CACHED; --strict reuses only passes recorded under a full,
every-byte signature, and --no-cache runs everything. Non-strict runs fingerprint the tree from a
stat cache (see tree_sig). Each check gets VERIFY_SLOT and a free VERIFY_PORT for --jobs.

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
  python scripts/verify.py run  [repo] [--only TEXT] [--timeout 120] [--strict] [--budget 5] [--jobs N] [--no-cache]
  python scripts/verify.py baseline [repo] [--reviewed-by NAME --reason WHY]
  python scripts/verify.py status   [repo] [--json]
  python scripts/verify.py report   [repo] [--json]
  python scripts/verify.py tests    [repo] [--strict]
  python scripts/verify.py scope PATH... [--add | --clear | --check] [--repo .]

Exit: run 0 = no check failed; 1 = a check failed (or --strict and something is unverified or
unproven, or has orphan tests); 2 = no usable VERIFY.md. Summary line:
  VERIFY: <f> features | <p> checks pass, <x> fail | <u> unverified | <n> unproven | <o> orphan tests | <j> journeys, <b> broken
"""
import argparse, ast, contextlib, fnmatch, hashlib, json, os, queue, random, re, shutil, signal, socket, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams
import gates

RECIPE = "VERIFY.md"
GENERIC_DIRS = {"tests", "test", "__tests__", "spec", "specs", "e2e", "integration", "unit"}
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target",
             "vendor", ".tox", "fixture", "fixtures", ".wire", ".debug", ".structure", ".threat", ".evolve", ".perf",
             ".release"}
TEST_PY = re.compile(r"^(test_.+|.+_test)\.py$")
TEST_JS = re.compile(r"^.+\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$")
TEST_GO = re.compile(r"^.+_test\.go$")
TAIL_LINES = 12
STATE = ".verify-state.json"
# The tree signature skips installed dependencies and build output, not test fixtures: a fixture is
# an input, and the result cache must not reuse a pass after one changes.
TREE_SKIP = SKIP_DIRS - {"fixture", "fixtures"}
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


def requirements(text):
    """Top-level `require:` lines (outside any section), e.g. `require: challenge`. Lower-cased words."""
    words, in_section = set(), False
    for line in text.splitlines():
        if re.match(r"^##\s", line):
            in_section = True
        m = re.match(r"^require:\s*(.+)$", line.strip()) if not in_section else None
        if m:
            words.update(w.strip().lower() for w in m.group(1).split(",") if w.strip())
    return sorted(words)


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
                       "journey": bool(j), "members": [], "oracles": [], "signals": [], "paths": [],
                       "fresh": None}
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
        elif kind == "fresh":
            cur["fresh"] = val
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
            if TEST_PY.match(f) or TEST_JS.match(f) or TEST_GO.match(f):
                found.append(os.path.relpath(os.path.join(root, f), repo).replace("\\", "/"))
    return sorted(found)


def is_covered(rel, commands, repo):
    """True when some command names this test file, a directory that holds it, or (Python) its
    module: `python -m unittest tests.test_x` or `pytest test_x` name tests/test_x.py."""
    base = rel.rsplit("/", 1)[-1]
    dotted = rel[:-3].replace("/", ".") if rel.endswith(".py") else None
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
            if dotted and "/" not in t and (
                    t == dotted or t.startswith(dotted + ".") or dotted.endswith("." + t)
                    or any(t.startswith(tail + ".") for tail in _module_tails(dotted))):
                return True
    return False


def _module_tails(dotted):
    """'a.b.test_x' -> ['b.test_x', 'test_x']: the module as named from a subfolder."""
    parts = dotted.split(".")
    return [".".join(parts[i:]) for i in range(1, len(parts))]


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
    return {c for c in changed if not any(is_state_file(part) for part in c.split("/"))}


def is_feature_affected(feature, changed_files, repo, covmap=None):
    """True if feature's checks, oracles, declared paths, or test files intersect with changed_files,
    or a check's recorded coverage (run --record-coverage) executed one of them."""
    if not changed_files:
        return True
    for _, cmd in feature["checks"]:
        entry = (covmap or {}).get(f"{feature['name']}|{cmd}")
        if isinstance(entry, dict) and entry.get("measured") and set(entry.get("files", [])) & set(changed_files):
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


def filter_affected(features, changed_files, repo, covmap=None):
    affected_names = set()
    for f in features:
        if not f["journey"] and is_feature_affected(f, changed_files, repo, covmap):
            affected_names.add(f["name"].lower())
    filtered = []
    for f in features:
        if f["journey"]:
            if any(m.lower() in affected_names for m in f["members"]):
                filtered.append(f)
        elif f["name"].lower() in affected_names:
            filtered.append(f)
    return filtered


# ---- the coverage map ---------------------------------------------------------------------
# File names in commands miss what a check imports. `run --record-coverage` runs each check with a
# stdlib sitecustomize on PYTHONPATH that hooks sys.setprofile in every Python process it spawns and
# records the repo files executed (O(1) set lookup per seen file, zero external dependencies).
# `--affected` then selects a feature when a changed file is in that set, as well as by the name
# heuristic. Non-Python checks record `measured: false` and keep the heuristic. Data files and new
# imports can still be missed, which is why --affected never makes --strict green.

SITECUSTOMIZE = """import os, sys
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.environ.get("VERIFY_COV_ROOT", "")
_seen, _called = set(), set()
_out = os.path.join(_here, f"covdata.{os.getpid()}")
_calls = os.path.join(_here, f"covcall.{os.getpid()}")
if _root:
    try:
        open(_out, "a", encoding="utf-8").close()
    except OSError:
        pass
    def _note(code):
        fn = code.co_filename
        func = bool(code.co_flags & 0x2)  # CO_NEWLOCALS: a function body, not module or class code
        if not fn or fn.startswith("<") or (fn in _called if func else fn in _seen):
            return
        try:
            real = os.path.realpath(fn)
            rel = os.path.relpath(real, _root)
            inside = not rel.startswith("..") and os.path.dirname(real) != _here
            for done, path in ((_seen, _out), (_called, _calls) if func else (None, None)):
                if done is not None and fn not in done:
                    done.add(fn)
                    if inside:
                        with open(path, "a", encoding="utf-8") as fh:
                            fh.write(rel.replace(os.sep, "/") + "\\n")
        except Exception:
            pass
    _mon = getattr(sys, "monitoring", None)
    try:  # 3.12+: each code object reports its first start, then costs nothing
        _mon.use_tool_id(4, "verify-coverage")
        def _start(code, offset):
            _note(code)
            return _mon.DISABLE
        _mon.register_callback(4, _mon.events.PY_START, _start)
        _mon.set_events(4, _mon.events.PY_START)
    except Exception:
        def _prof(frame, event, arg):
            if event == "call":
                _note(frame.f_code)
        sys.setprofile(_prof)
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _here]
del sys.modules["sitecustomize"]
try:
    import sitecustomize  # the one this file shadows, if any
except ImportError:
    pass
"""


def has_coverage():
    return True


def coverage_path(repo):
    return os.path.join(cache_dir(repo), "coverage.json")


def coverage_env(folder, repo):
    """Environment additions that make every Python process a check starts record into `folder`."""
    with open(os.path.join(folder, "sitecustomize.py"), "w", encoding="utf-8") as fh:
        fh.write(SITECUSTOMIZE)
    path = os.environ.get("PYTHONPATH")
    return {"VERIFY_COV_ROOT": os.path.realpath(repo),
            "PYTHONPATH": folder + (os.pathsep + path if path else "")}


def coverage_files(folder, repo):
    """{measured, files, called}: the repo-relative files the check's Python processes executed,
    and the ones where a function (not just module or class code, as an import runs) was called."""
    files, called, measured = set(), set(), False
    for name in os.listdir(folder):
        into = files if name.startswith("covdata") else called if name.startswith("covcall") else None
        if into is None:
            continue
        measured = measured or into is files
        with open(os.path.join(folder, name), encoding="utf-8", errors="replace") as fh:
            into.update(ln.strip() for ln in fh if ln.strip())
    return {"measured": measured, "files": sorted(files), "called": sorted(called)}


# ---- hollow passes ------------------------------------------------------------------------
# A check can exit 0 without running the product: it loads no cases, loops over [], skips, or
# tests a copy of the logic. When a feature names Python files with functions in `path:`, `run`
# measures its checks and calls the feature HOLLOW if they all pass without calling one of those
# functions. Importing the module does not count: an import runs module code, not the behavior.

INFER = "infer"  # no `path:`: the product is whatever repo code the checks imported


def is_test_file(rel):
    base = rel.rsplit("/", 1)[-1]
    return bool(TEST_PY.match(base)) or base == "conftest.py" or any(
        part in SKIP_DIRS for part in rel.split("/")[:-1])


def defines_function(repo, rel):
    try:
        tree = ast.parse(read(repo, rel))
    except (SyntaxError, ValueError, OSError):
        return False
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))


def reach_targets(repo, feature):
    """Repo-relative .py files under the feature's `path:` that define a function (empty = not
    judged), or INFER when the feature has no `path:`."""
    if not feature.get("paths"):
        return INFER
    out = set()
    for p in feature["paths"]:
        p = p.strip().rstrip("/").replace("\\", "/")
        full = os.path.join(repo, p)
        found = [p] if os.path.isfile(full) else []
        if os.path.isdir(full):
            for here, dirs, files in os.walk(full):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                found += [os.path.relpath(os.path.join(here, f), repo).replace("\\", "/") for f in files]
        out |= {rel for rel in found if rel.endswith(".py") and not is_test_file(rel) and defines_function(repo, rel)}
    return out


def hollow(repo, targets, rows, reach):
    """The product files the feature's checks should have called, when every check passed, ran
    fresh under measurement, and called no function in them; else []. Cached or unmeasured
    (non-Python) checks leave it unjudged. With INFER (no `path:`) the product is the non-test repo
    code the checks imported, and calling any function in any of it clears the feature."""
    if not targets or not rows:
        return []
    entries = []
    for cmd, ok, cached in rows:
        entry = reach.get(cmd)
        if not ok or cached or not entry or not entry.get("measured"):
            return []
        entries.append(entry)
    called = {f for e in entries for f in e.get("called", [])}
    if targets == INFER:
        if any(not is_test_file(f) for f in called):
            return []
        return sorted({f for e in entries for f in e.get("files", []) if f.endswith(".py")
                       and not is_test_file(f) and defines_function(repo, f)})
    return [] if targets & called else sorted(targets)


# ---- fresh inputs -------------------------------------------------------------------------
# Mutation testing and HOLLOW judge the check; neither sees product code that special-cases the
# inputs the check was written with (`if x == 3: return 9` catches every mutant on that line). A
# feature with `fresh: N` has its passing checks run N more times, each with a random VERIFY_SEED
# the check draws its cases from. A product that passes its own cases and fails a fresh one is
# OVERFIT. The own cases always run with no seed, so they stay the ones the check was written with.

SEED = "VERIFY_SEED"
FRESH_MAX = 20


def fresh_count(raw):
    """(runs, error) for a `fresh:` value; (0, None) when the feature declares none."""
    if raw is None:
        return 0, None
    if raw.isdigit() and 1 <= int(raw) <= FRESH_MAX:
        return int(raw), None
    return 0, f"wants a number of seeded runs (1-{FRESH_MAX}), got '{raw}'"


def no_fresh_inputs(features, recipe_text):
    """Features `require: fresh` holds red: every feature with checks that declares no `fresh:`."""
    if "fresh" not in requirements(recipe_text):
        return []
    return [f["name"] for f in features if not f["journey"] and f["checks"] and f["fresh"] is None]


def reads_seed(repo, feature):
    """True when a test file, script or oracle of the feature names VERIFY_SEED. A check that never
    reads it repeats its own cases on every fresh run, which proves nothing new."""
    cmds = [c for _, c in feature["checks"]]
    files = set(feature["oracles"]) | {t for t in find_tests(repo) if is_covered(t, cmds, repo)}
    for cmd in cmds:
        files |= {tok.strip("\"'") for tok in re.findall(r'"[^"\n]*"|\'[^\'\n]*\'|[^\s]+', cmd)}
    if any(SEED in c for c in cmds):
        return True
    for rel in files:
        if os.path.isfile(os.path.join(repo, rel)):
            try:
                if SEED in read(repo, rel):
                    return True
            except (OSError, ValueError):
                continue
    return False


def fresh_runs(repo, feature, runs, timeout):
    """(seeds that passed, failure or None): each check again under `runs` random seeds, stopping at
    the first red. A failure is {kind, command, seed, exit, output}."""
    pick, passed = random.SystemRandom(), []
    for _ in range(runs):
        seed = pick.randrange(1, 2 ** 31)
        for kind, cmd in feature["checks"]:
            ok, code, out, _ = run_check(cmd, repo, timeout, dict(os.environ, **{SEED: str(seed)}))
            if not ok:
                return passed, {"kind": kind, "command": cmd, "seed": seed, "exit": code, "output": out[-4000:]}
        passed.append(seed)
    return passed, None


def save_survey(repo, feature, entry):
    """Keep the last `challenge --auto` score per feature in the cache, outside .verify-state.json:
    a survey is a lead, so it leaves the verification state as it found it."""
    path = os.path.join(cache_dir(repo), "surveys.json")
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with file_lock(path + ".lock"):
            data = read_json(path)
            data[feature] = entry
            write_json(path, data)
    except (OSError, TimeoutError) as exc:
        print(f"note  survey score not saved: {exc}")


def save_coverage(repo, entries):
    if not entries:
        return
    path = coverage_path(repo)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with file_lock(path + ".lock"):
            data = read_json(path)
            data.update(entries)
            write_json(path, data)
    except (OSError, TimeoutError) as exc:
        print(f"note  coverage map not saved: {exc}")


SELECTED = ("SELECTED  --affected chose checks by changed files and can miss one (an import, a data "
            "file): a strict verdict needs the whole run, without --affected")


# ---- the per-test map ---------------------------------------------------------------------
# `run` maps test FILES to features. A file with forty tests is one row there, so a hollow test
# hides inside a verified feature. `tests` goes down to the function: every test under the
# feature whose command names its file, and the ones that can never go red flagged. Static (it
# parses, it runs nothing), Python only.

ASSERTING = ("assert", "fail", "raises", "warns")


def _call_name(node):
    f = node.func
    return f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""


def _assert_count(fn, helpers):
    """Assertions in the function, direct or by calling a helper that has one."""
    return sum(isinstance(n, ast.Assert) or (isinstance(n, ast.Call) and (
        _call_name(n).lower().startswith(ASSERTING) or _call_name(n) in helpers)) for n in ast.walk(fn))


def _asserts(fn, helpers):
    """True if the function has an assertion, directly or by calling a helper that has one."""
    return _assert_count(fn, helpers) > 0


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


def _balanced_body(text, pos, open_ch="(", close_ch=")"):
    """Slice of `text` inside matching open_ch..close_ch starting at or after `pos`, or None."""
    depth, in_str, esc, start = 0, None, False, None
    for i in range(pos, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'", "`"):
            in_str = ch
            continue
        if ch == open_ch:
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0 and start is not None:
                return text[start:i]
    return None


def _js_tests_in(text):
    from mutate import is_balanced_delimiters
    if not is_balanced_delimiters(text):
        return None
    assert_rx = re.compile(r"\b(?:expect|assert|should)\b|\.(?:toBe|toEqual|toMatch|toThrow|rejects)\b")
    swallow_rx = re.compile(r"\btry\s*\{[^{}]*\}\s*catch\b[^{]*\{\s*\}")
    helpers = {m.group(1) for m in re.finditer(r"\bfunction\s+(\w+)\s*\([^)]*\)\s*\{", text)
               if assert_rx.search(_balanced_body(text, m.end() - 1, "{", "}") or "")}
    found = []
    for m in re.finditer(r"(?m)(?:^|[;{]\s*)(?:(x(?:it|test)|(?:it|test)\.(?:skip|todo))|(it|test))\s*\(\s*(['\"`])((?:\\.|(?!\3).)+)\3", text):
        skip, name = bool(m.group(1)), m.group(4)
        body = _balanced_body(text, m.start(), "(", ")") or ""
        count = len(assert_rx.findall(body)) + sum(len(re.findall(rf"\b{re.escape(h)}\s*\(", body)) for h in helpers)
        has_assert = count > 0
        flag = ("passes either way: it catches the exception and never fails"
                if swallow_rx.search(body) and not has_assert else "" if has_assert else "no assertion")
        found.append((name, flag, skip, count))
    return found


def _go_tests_in(text):
    from mutate import is_balanced_delimiters
    if not is_balanced_delimiters(text):
        return None
    found = []
    for m in re.finditer(r"(?m)^\s*func\s+(Test\w+)\s*\(\s*(\w+)\s+\*testing\.T\s*\)\s*\{", text):
        name, tvar = m.group(1), re.escape(m.group(2))
        body = _balanced_body(text, m.end() - 1, "{", "}") or ""
        skip = bool(re.search(rf"\b{tvar}\.Skip(?:Now|f)?\s*\(", body))
        count = len(re.findall(rf"\b{tvar}\.(?:Fatal|Fatalf|Error|Errorf|Fail|FailNow)\s*\(|\b(?:assert|require)\.\w+\s*\(", body))
        found.append((name, "" if count else "no assertion", skip, count))
    return found


def tests_in(repo, rel):
    """[(name, flag, skipped)] for the test functions in one Python, JS/TS or Go file; flag is '' or a reason.
    None when the file cannot be parsed."""
    found = tests_in_text(read(repo, rel), rel)
    return None if found is None else [row[:3] for row in found]


def tests_in_text(text, rel):
    """tests_in for file content: [(name, flag, skipped, assertion count)], or None if unparsable.
    `review` compares these between a base and the working tree."""
    base = rel.rsplit("/", 1)[-1]
    if TEST_JS.match(base):
        return _js_tests_in(text)
    if TEST_GO.match(base):
        return _go_tests_in(text)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    defs = (ast.FunctionDef, ast.AsyncFunctionDef)
    helpers = set()
    for _ in range(2):
        helpers |= {n.name for n in ast.walk(tree) if isinstance(n, defs)
                    and not n.name.startswith("test") and _asserts(n, helpers)}
    found = []

    def take(fn, name):
        count = _assert_count(fn, helpers)
        if _swallows(fn):
            flag = "passes either way: it catches the exception and never fails"
        elif not count:
            flag = "no assertion"
        else:
            flag = ""
        found.append((name, flag, _skipped(fn), count))

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
    per_file, bad = {}, []
    for t in files:
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
        "require: challenge",
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


def run_check(cmd, repo, timeout, env=None):
    """(ok, exit code or None, combined output, seconds)."""
    t0 = time.time()
    run_env = dict(os.environ if env is None else env)
    if env is None:
        run_env.pop(SEED, None)  # only a fresh run sets the seed
    run_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    try:
        p = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=run_env)
        return p.returncode == 0, p.returncode, (p.stdout or "") + (p.stderr or ""), time.time() - t0
    except subprocess.TimeoutExpired:
        return False, None, f"timed out after {timeout}s", time.time() - t0


def attempt(cmd, repo, timeout, stress, env=None):
    """(ok, exit, output, seconds, passes) for one check; with stress > 1 it repeats and counts passes."""
    ok, code, out, secs = run_check(cmd, repo, timeout, env)
    passes = int(ok)
    for _ in range(stress - 1):
        passes += run_check(cmd, repo, timeout, env)[0]
    return ok, code, out, secs, passes


def free_port():
    """A TCP port nothing listens on right now (the OS picks it)."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def slotted(jobs, repo, timeout, stress, record=None, measure=()):
    """attempt() for run --jobs: each check runs with VERIFY_SLOT (0..jobs-1, never two running
    checks in one slot) and a fresh VERIFY_PORT, so checks that start their own app, database or
    scratch folder can key it on those and run in parallel without colliding. With `record` (a
    dict), each check also runs under coverage and record[cmd] gets the files it executed; with
    `measure` (commands) only those do."""
    slots = queue.Queue()
    for i in range(max(1, jobs)):
        slots.put(i)

    def run_one(cmd):
        slot = slots.get()
        try:
            env = dict(os.environ, VERIFY_SLOT=str(slot), VERIFY_PORT=str(free_port()))
            env.pop(SEED, None)  # the own cases: the ones the check was written with
            if record is None or (measure and cmd not in measure):
                return attempt(cmd, repo, timeout, stress, env)
            with tempfile.TemporaryDirectory(prefix="verify-cov-") as folder:
                env.update(coverage_env(folder, repo))
                result = attempt(cmd, repo, timeout, stress, env)
                try:
                    record[cmd] = coverage_files(folder, repo)
                except Exception as exc:  # unreadable data: keep the heuristic for this check
                    record[cmd] = {"measured": False, "files": [], "error": str(exc)[:200]}
                return result
        finally:
            slots.put(slot)
    return run_one


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
    app_env = dict(os.environ)
    app_env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    with os.fdopen(fd, "w") as fh:
        proc = subprocess.Popen(run_cmd, shell=True, cwd=repo, stdout=fh, stderr=subprocess.STDOUT, env=app_env, **kw)
    return proc, log


def stop_app(proc, stop_cmd, repo, timeout):
    result = (True, 0, "", 0)
    if stop_cmd:
        result = run_check(stop_cmd, repo, timeout)
    if proc is not None and proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
    if proc is not None:
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            return False, None, "owned process did not stop", 10
    return result


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


def cmd_run(repo, only, timeout, strict, budget=BUDGET, affected=None, stress=1, as_json=False, quarantine=False, jobs=1,
            use_cache=True, record_coverage=False, judge_reach=True):
    """judge_reach=False: no HOLLOW verdict, for the scratch reruns inside challenge, whose own
    verdict (survived) is the more useful answer about a check that never runs the product."""
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
        covmap = read_json(coverage_path(repo))
        if changed_files:
            features = filter_affected(features, changed_files, repo, covmap)
        if not changed_files or not features:
            detail = (f"no files changed vs {affected}" if not changed_files
                      else f"{len(changed_files)} changed file(s) touched no mapped features")
            code = 1 if strict else 0
            if as_json:
                print(json.dumps({
                    "verdict": "red" if strict else "green", "detail": detail, "exit": code, "strict": strict,
                    "selected": True, "summary": {"features": 0, "passed": 0, "failed": 0}, "results": [],
                }, indent=2))
            else:
                print(f"AFFECTED: {detail}; nothing to run.")
                if strict:
                    print(SELECTED)
            return code
        if not as_json:
            mapped = sum(1 for f in features for _, c in f["checks"]
                         if (covmap.get(f"{f['name']}|{c}") or {}).get("measured"))
            print(f"AFFECTED: running {len(features)} feature(s) affected by {len(changed_files)} changed file(s)"
                  + (f"; {mapped} of their checks have a coverage map." if mapped else "."))
    record = None
    if record_coverage:
        if has_coverage():
            record, use_cache = {}, False
        elif not as_json:
            print("note  --record-coverage: coverage.py is not importable, so no map was recorded; "
                  "--affected keeps matching file names. `pip install coverage` to use it.")

    try:
        hashes = check_hashes(repo)
    except (OSError, ValueError) as exc:
        if as_json:
            print(json.dumps({"error": f"Run: invalid oracle: {exc}", "exit": 1}))
        else:
            print(f"Run: invalid oracle: {exc}; no check was run.")
        track(repo, [], only, budget, 1, strict)
        return 1

    recipe = parse_run(read(repo, RECIPE))
    # Without a ## Run recipe nothing runs between here and the checks, so the hashes just
    # computed are the run's signature; setup or an app start could still rewrite a frozen file.
    signature = None if recipe else sha(json.dumps(hashes, sort_keys=True))
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
    verdict = 1
    reports = []
    try:
        if recipe and recipe.get("doctor"):
            ok, code, out, secs = run_check(recipe["doctor"], repo, timeout)
            state = load_state(repo)
            state["doctor"] = {"ok": ok, "exit": code, "output": out[-4000:], "seconds": secs}
            save_state(repo, state)
            if not ok:
                if as_json:
                    reports.append({"error": "Run: doctor failed", "exit": 1, "output": out[-1000:]})
                else:
                    print("Run: doctor failed; no check was run.")
                    for line in out.rstrip().splitlines()[-TAIL_LINES:]:
                        print(f"        {line}")
                track(repo, [], only, budget, 1, strict)
            else:
                verdict = run_checks(repo, features, blind, recipe, only, timeout, strict, budget, stress, as_json, quarantine, reports, jobs, signature, use_cache,
                                     affected is not None, record, judge_reach)
        else:
            verdict = run_checks(repo, features, blind, recipe, only, timeout, strict, budget, stress, as_json, quarantine, reports, jobs, signature, use_cache,
                                     affected is not None, record, judge_reach)
    finally:
        if proc or (recipe and recipe.get("stop")):
            ok, code, out, secs = stop_app(proc, recipe.get("stop"), repo, timeout)
            state = load_state(repo)
            state["cleanup"] = {"ok": ok, "exit": code, "output": out[-4000:], "seconds": secs}
            if not ok:
                state["result"] = "red"
                verdict = 1
                if not as_json:
                    print("Run: cleanup failed")
                    print(out[-4000:])
                elif reports:
                    reports[-1].update({"verdict": "red", "exit": 1, "error": "Run: cleanup failed",
                                        "cleanup": state["cleanup"]})
            save_state(repo, state)
        if log:
            try:
                os.unlink(log)
            except OSError:
                pass
    if as_json and reports:
        print(json.dumps(reports[-1], indent=2))
    return verdict


def run_checks(repo, features, blind, recipe, only, timeout, strict, budget=BUDGET, stress=1, as_json=False, quarantine=False, reports=None, jobs=1, signature=None, use_cache=True,
               selected=False, record=None, judge_reach=True):
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
    signature = signature or sha(json.dumps(check_hashes(repo), sort_keys=True))
    receipts = current_receipts(state, signature)
    red_now = set()
    where = proof_where(repo, red_now) if strict else None
    # The result cache: a pass some agent proved for this command on this exact content is reused.
    # Not with a ## Run recipe (checks then depend on a live app) or --stress (which must re-run).
    caching = use_cache and not recipe and stress == 1
    tree_before = tree_sig(repo, fast=not strict) if caching else None
    sig_info = dict(TREE_INFO) if caching else None
    hits = cached_passes(repo, {c for f in shown for _, c in f["checks"]}, tree_before, strict) if caching else {}
    fresh = {}  # command: (output, seconds) for passes this run proved
    # --jobs: start every check now, then read results in recipe order, so output and loop memory
    # are the same as a serial run. Default 1: checks that share an app or files may collide.
    order = [cmd for f in shown for _, cmd in f["checks"]]
    # Judged: features whose checks are all `test:` with no ## Run recipe. A `run:` check or one
    # against a started app drives a process the measurement does not see.
    targets = {f["name"]: reach_targets(repo, f) for f in shown if judge_reach and not f["journey"] and not recipe
               and f["checks"] and all(k == "test" for k, _ in f["checks"])}
    measure = {c for f in shown if targets.get(f["name"]) for _, c in f["checks"]}
    reach = record if record is not None else {}
    run_one = slotted(jobs, repo, timeout, stress, reach if (record is not None or measure) else None,
                      () if record is not None else measure)
    hollow_feats = []
    overfit, seed_unused = {}, []  # feature: the fresh run that went red; features whose checks ignore the seed
    pending = {}
    if jobs > 1:
        pool = ThreadPoolExecutor(max_workers=jobs)
        pending = {i: pool.submit(run_one, cmd)
                   for i, cmd in enumerate(order) if cmd not in hits}
        pool.shutdown(wait=False)  # submitted checks still run; results are read below
    index = -1
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
            index += 1
            hit = hits.get(cmd)
            if hit:
                ok, code, out, secs, check_passes = True, 0, hit.get("output", ""), 0.0, 1
            else:
                job = pending.pop(index, None)
                ok, code, out, secs, check_passes = job.result() if job else run_one(cmd)
                if ok and caching:
                    fresh[cmd] = (out, secs)
            if stress > 1 and 0 < check_passes < stress:
                flaky_checks.append((f["name"], kind, cmd, check_passes, stress))
                quarantined.add(f"{f['name']}|{cmd}")
                ok = False

            key = f"{f['name']}|{cmd}"
            is_quarantined = False
            if not ok and quarantine and (key in quarantined) and not strict:
                is_quarantined = True
                quarantined_hits.append((f["name"], kind, cmd))

            results.append((f["name"], kind, cmd, ok, out, code, is_quarantined, bool(hit)))
            if not ok:
                red_now.add(key)
            if is_quarantined:
                if not as_json:
                    print(f"  QUARANTINED  {kind}  {cmd}  [{secs:.1f}s] (flake isolated)")
            else:
                passed += ok
                failed += not ok
                if not as_json:
                    tag = "PASS" if ok else "FAIL"
                    extra = "" if ok else (" (timeout)" if code is None else f" (exit {code})")
                    when = (f"CACHED: proved {hit.get('at')} by {hit.get('agent') or 'an unnamed agent'}"
                            if hit else f"{secs:.1f}s")
                    print(f"  {tag}  {kind}  {cmd}  [{when}]{extra}")
                    if not ok:
                        cause = extract_failure_summary(out)
                        if cause:
                            print(f"        CAUSE  {cause}")
                        env = gates.blocked(sys.modules[__name__], out, code)
                        if env:
                            print(f"        BLOCKED  {env} The environment failed, not the product: report the "
                                  "check as blocked and name where it does run. Do not change product code for it")
                        for line in out.rstrip().splitlines()[-TAIL_LINES:]:
                            print(f"        {line}")
        mine = [(c, ok_r, hit_r) for fn, _, c, ok_r, _, _, q_r, hit_r in results if fn == f["name"] and not q_r]
        missed = hollow(repo, targets.get(f["name"]), mine, reach)
        if missed:
            hollow_feats.append(f["name"])
            for c, _, _ in mine:
                fresh.pop(c, None)
            if not as_json:
                print(f"  HOLLOW  every check passed without calling a function in {', '.join(missed)}"
                      + (" (imported, never called)" if targets[f["name"]] == INFER else "")
                      + ": it loads no cases, skips, or tests a copy. A pass that never runs the product "
                      "proves nothing about it")
        runs, bad_fresh = fresh_count(f["fresh"])
        if bad_fresh:
            broken += 1
            if not as_json:
                print(f"  BROKEN  fresh: {bad_fresh}")
        elif runs and judge_reach and not reads_seed(repo, f):
            seed_unused.append(f["name"])
            if not as_json:
                print(f"  SEED UNUSED  `fresh: {runs}` is declared, but no test, script or oracle of this feature "
                      f"reads {SEED}: every fresh run would repeat the own cases. Draw the cases from the seed, "
                      "and the expected values from the spec, not from the product")
        elif runs and judge_reach and mine and all(ok_r for _, ok_r, _ in mine):
            seeds, miss = fresh_runs(repo, f, runs, timeout)
            if miss:
                overfit[f["name"]] = {k: miss[k] for k in ("kind", "command", "seed", "exit")}
                for c, _, _ in mine:
                    fresh.pop(c, None)
                if not as_json:
                    print(f"  OVERFIT  {miss['kind']}  {miss['command']}: passed its own cases, failed on fresh "
                          f"inputs ({SEED}={miss['seed']}"
                          + (", timeout" if miss["exit"] is None else f", exit {miss['exit']}") + "). The product "
                          "may special-case the inputs the check was written with. Fix the product, not the check. "
                          f"Reproduce: {SEED}={miss['seed']} {miss['command']}")
                    cause = extract_failure_summary(miss["output"])
                    if cause:
                        print(f"        CAUSE  {cause}")
                    for line in miss["output"].rstrip().splitlines()[-TAIL_LINES:]:
                        print(f"        {line}")
            elif not as_json:
                print(f"  FRESH  {len(seeds)} seeded run(s) passed ({SEED}={', '.join(map(str, seeds))})")
        if not as_json:
            for sig in f["signals"]:
                why = gates.weak_signal(sig)
                if why:
                    print(f"  WEAK SIGNAL  `{sig}`: {why}")
        if not f["proofs"]:
            unproven += 1
            if not as_json:
                print("  note  no fail-proof recorded: nobody has shown these checks can go red")
        elif strict:
            passing_out = {f"{fn}|{c}": o for fn, _, c, ok_r, o, *_ in results if ok_r and fn == f["name"]}
            if not proven_by(f, receipts, signature, passing_out, where):
                unproven += 1
                if not as_json:
                    if f["signals"] and all(gates.weak_signal(sig) for sig in f["signals"]):
                        print("  note  no fail-signal that names a behavior, so no receipt can prove rejection")
                    elif proven_by(f, receipts, signature, passing_out):
                        print(f"  PROOF NOT FROM PRODUCT  {where_reason(f, receipts, where)}")
                    elif proven_by(f, receipts, signature):
                        print("  SIGNAL IN PASS  fail-signal also appears in passing output: a signal printed on pass cannot prove rejection")
                    else:
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
    unmapped, loose = [], []
    if not only and not selected:
        unmapped = gates.unmapped(sys.modules[__name__], repo, features, blind)
        if strict:
            loose = gate_findings_loosened(repo, features, state)
    if not as_json:
        for rel in unmapped:
            print(f"UNMAPPED  {rel}: product code no feature's path:, command or checked imports reach. "
                  "Map it to a feature in VERIFY.md, or name it under ## Blind spots and say why")
        for x in loose:
            print(f"LOOSENED  {gates.loosened_text(x)}. A weaker check is a finding, not a fix: restore it, "
                  "or have a person review it and run `verify.py baseline --reviewed-by <name> --reason <why>`")
        if blind:
            print("Blind spots (a green run does not cover these):")
            for b in blind:
                print(f"  - {b}")
        else:
            print("Blind spots: none listed. A recipe that admits none has not looked.")

    unchallenged = (strict and "challenge" in requirements(read(repo, RECIPE)) and not any(
        r.get("mutation") and r.get("signature") == signature for r in receipts.values()))
    if unchallenged and not as_json:
        print("UNCHALLENGED  VERIFY.md requires a caught mutation for the current checks: run "
              "`verify.py challenge` on the highest-risk feature")
    no_fresh = no_fresh_inputs(shown, read(repo, RECIPE)) if strict else []
    if not as_json:
        for name in no_fresh:
            print(f"NO FRESH INPUTS  {name}: VERIFY.md has `require: fresh` and this feature has no `fresh: N`, so "
                  f"nothing shows the product handles inputs its check was not written with. Add `fresh:` and draw "
                  f"the check's cases from {SEED}")
    try:
        changed_during_run = signature != sha(json.dumps(check_hashes(repo), sort_keys=True))
    except (OSError, ValueError):
        changed_during_run = True
    if changed_during_run and not as_json:
        print("CHECK CHANGED DURING RUN  repeat verification with stable checks and oracles")
    tree_after = tree_sig(repo, fast=not strict) if caching else (tree_sig(repo, fast=False) if strict else None)
    runner = agent_name()
    if strict and runner and not only and not selected and not changed_during_run:
        frozen_map = state.get("frozen_by") or {}
        v_by = state.setdefault("verified_by", {})
        for feat_n, kind, cmd, ok_r, _, _, q_r, _ in results:
            ckey = f"{feat_n}|{kind}|{cmd}"
            if ok_r and not q_r and frozen_map.get(ckey) not in (None, runner):
                v_by[ckey] = {"agent": runner, "signature": signature, "tree": tree_after}
    dependent = (not_independent(state, shown, runner, signature, tree_after)
                 if strict and "independent" in requirements(read(repo, RECIPE)) else [])
    if not as_json:
        for feat, kind, cmd, who in dependent:
            print(f"NOT INDEPENDENT  {feat} ({kind}): frozen by {who or 'an unnamed agent'}, run by "
                  f"{runner or 'an unnamed agent'}. VERIFY.md requires the agent that froze a check to "
                  "differ from the one claiming green: have a separate VERIFY_AGENT run `baseline` or this run")
    if strict and selected and not as_json:
        print(SELECTED)
    incomplete = strict and (unverified or unproven or orphans or missing_baseline or unchallenged or dependent
                             or selected or unmapped or loose or no_fresh)
    if caching and tree_after == tree_before and not changed_during_run:
        remember_passes(repo, fresh, tree_before, full=strict)
    cached = sum(1 for r in results if r[7])
    recorded = {}
    if record is not None:
        at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        recorded = {f"{f['name']}|{c}": dict(record[c], at=at) for f in shown for _, c in f["checks"] if c in record}
        save_coverage(repo, recorded)
        if not as_json:
            blind_checks = sum(1 for e in recorded.values() if not e["measured"])
            print(f"COVERAGE  recorded the files {len(recorded)} check(s) execute; --affected selects by them"
                  + (f" ({blind_checks} measured nothing: not Python, or no coverage.py in their interpreter)"
                     if blind_checks else ""))
    if quarantined:
        state["quarantined"] = sorted(quarantined)
    if state.get("verified_by") or quarantined:
        save_state(repo, state)
    norm_results = [(feat, kind, cmd, (ok or q), out, code) for feat, kind, cmd, ok, out, code, q, _ in results]
    notes, bad = track(repo, norm_results, only, budget,
                       failed + broken + bool(incomplete) + changed_during_run + bool(flaky_checks) + len(hollow_feats)
                       + len(overfit) + len(seed_unused),
                       strict, signature,
                       tree_after)
    verify_line = (f"VERIFY: {len(shown) - journeys} features | {passed} checks pass, {failed} fail | "
                   f"{unverified} unverified | {unproven} unproven | {len(orphans)} orphan tests | "
                   f"{journeys} journeys, {broken} broken" + (f" | {len(hollow_feats)} hollow" if hollow_feats else "")
                   + (f" | {len(overfit)} overfit" if overfit else "") + (f" | {len(seed_unused)} seed unused" if seed_unused else "")
                   + (f" | {len(unmapped)} unmapped" if unmapped else "") + (f" | {len(loose)} loosened" if loose else ""))
    if not only:
        state = load_state(repo)
        state["verify_line"] = verify_line
        if judge_reach:  # `report` turns a hollow, unfrozen check into a `repair` step
            ran = {f["name"] for f in shown}
            state["hollow"] = sorted((set(state.get("hollow") or []) - ran) | set(hollow_feats))
            state["overfit"] = dict({k: v for k, v in (state.get("overfit") or {}).items() if k not in ran}, **overfit)
            state["seed_unused"] = sorted((set(state.get("seed_unused") or []) - ran) | set(seed_unused))
        save_state(repo, state)
    if not as_json:
        for n in notes:
            print(n)
        print(verify_line)
        if quarantined_hits:
            print(f"  QUARANTINED: {len(quarantined_hits)} check(s) isolated from failure.")
        if cached:
            print(f"CACHED  {cached} check(s) reused: already proved passing on this exact content"
                  + (" (full signature)" if strict else "") + "; --no-cache runs them again")
    red = bool(failed or broken or bad or incomplete or changed_during_run or flaky_checks or hollow_feats
               or overfit or seed_unused)
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
                "hollow": hollow_feats,
                "overfit": sorted(overfit),
                "seed_unused": seed_unused,
                "unmapped": unmapped,
                "loosened": [gates.loosened_text(x) for x in loose],
                "unchallenged": bool(unchallenged),
                "no_fresh": no_fresh,
                "not_independent": len(dependent),
                "quarantined": len(quarantined_hits),
                "cached": cached,
                "coverage_recorded": sum(1 for e in recorded.values() if e["measured"]),
            },
            "selected": selected,
            "results": [
                {
                    "feature": feat, "kind": kind, "command": cmd, "ok": ok, "exit": code,
                    "cause": None if ok else extract_failure_summary(out),
                    "quarantined": q, "cached": c,
                }
                for feat, kind, cmd, ok, out, code, q, c in results
            ],
            "blind_spots": blind,
            "tree_sig": sig_info or dict(TREE_INFO),
            "verify_line": verify_line,
            "exit": 1 if red else 0,
        }
        if reports is None:
            print(json.dumps(report, indent=2))
        else:
            reports.append(report)
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


def seal_of(state):
    body = {k: v for k, v in state.items() if k != "seal"}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


# Many agents can share one checkout. Every save takes a short lock, re-reads the file and merges:
# a key this process did not change keeps what is on disk, so a stale save cannot revert another
# agent's baseline or drop its receipts. The file is replaced whole, so a reader never sees half of
# it. With VERIFY_AGENT=<name>, loop memory (last run, rounds, scope, doctor) lives in
# .verify-state.<name>.json; the baseline, re-baselines and rejection receipts stay in STATE for
# every agent, so a new name neither escapes a freeze nor has to re-prove a check.
SHARED_KEYS = ("baseline", "baseline_lines", "baseline_files", "rebaselines", "failures", "frozen_by", "verified_by", "swarm",
               "loosened_reviewed", "receipt_trees")
AGENT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
LOCK = ".verify-state.lock"
_loaded = {}  # state file -> what this process last read from it: the base of the merge


def is_state_file(name):
    """STATE, an agent's state file, the lock or a temp file mid-write."""
    return name.startswith(".verify-state")


def agent_name():
    name = os.environ.get("VERIFY_AGENT", "").strip()
    if name and not AGENT_NAME.match(name):
        raise ValueError(f"VERIFY_AGENT={name!r}: use 1-64 letters, digits, '-' or '_'")
    return name or None


# Assessing a repo should not change it. VERIFY_STATE_DIR (set by --state-dir or --assess) moves
# the state files, the lock and the caches to <dir>/<repo name>-<hash of its path>, one folder per
# repo. Scratch copies keep their state inside themselves, so it is deleted with them.
_IN_PLACE = set()


def keep_state_in(path):
    """A scratch copy: its state stays inside it even when VERIFY_STATE_DIR is set."""
    _IN_PLACE.add(os.path.realpath(path))


def assess_dir():
    """The default --assess state root: a per-user folder in the system temp directory."""
    return os.path.join(tempfile.gettempdir(), "verify-loop-assess")


def outside_home(repo):
    """The folder outside the repo that holds its state, or None when state lives in the repo."""
    root = os.environ.get("VERIFY_STATE_DIR", "").strip()
    real = os.path.realpath(repo)
    if not root or real in _IN_PLACE:
        return None
    return os.path.join(os.path.abspath(root), f"{os.path.basename(real) or 'repo'}-{sha(real)}")


def state_flag():
    """What a printed follow-up command needs to find the same state: ' --state-dir DIR' or ''."""
    root = os.environ.get("VERIFY_STATE_DIR", "").strip()
    return f' --state-dir "{os.path.abspath(root)}"' if root else ""


def state_home(repo):
    """Where the state files and the lock live: the repo, or its folder under VERIFY_STATE_DIR."""
    return outside_home(repo) or repo


def state_paths(repo):
    """(shared file, this agent's file); the same path when VERIFY_AGENT is unset."""
    home, name = state_home(repo), agent_name()
    shared = os.path.join(home, STATE)
    return shared, (os.path.join(home, f".verify-state.{name}.json") if name else shared)


def retry(fn, tries=100):
    """Windows refuses to replace or open a file another process holds for a moment: wait it out."""
    for i in range(tries):
        try:
            return fn()
        except PermissionError:
            if i == tries - 1:
                raise
            time.sleep(0.01)


def read_state_file(path):
    def load():
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    try:
        data = retry(load)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {"forged": True}
    if data and data.get("seal") != seal_of(data):
        data["forged"] = True
    data.pop("seal", None)
    return data


def load_state(repo):
    """The saved state. A file whose seal does not match was written by something other than this
    script; it comes back marked `forged`, and the mark survives every later save until the file is
    deleted. The seal has no secret: it catches hand edits, not a writer who recomputes it.
    Independently owned CI is what a determined writer cannot reach."""
    shared_path, own_path = state_paths(repo)
    shared = read_state_file(shared_path)
    _loaded[shared_path] = json.loads(json.dumps(shared))
    if own_path == shared_path:
        return shared
    own = read_state_file(own_path)
    _loaded[own_path] = json.loads(json.dumps(own))
    data = {k: v for k, v in own.items() if k not in SHARED_KEYS}
    data.update({k: shared[k] for k in SHARED_KEYS if k in shared})
    if shared.get("forged"):
        data["forged"] = True
    return data


def state_lock(repo, wait=30.0, stale=60.0):
    home = state_home(repo)
    os.makedirs(home, exist_ok=True)
    return file_lock(os.path.join(home, LOCK), wait, stale)


@contextlib.contextmanager
def file_lock(path, wait=30.0, stale=60.0):
    """Held only while one save merges and writes, so a lock older than `stale` is abandoned."""
    end = time.time() + wait
    while True:
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except (FileExistsError, PermissionError):
            try:
                if time.time() - os.path.getmtime(path) > stale:
                    os.remove(path)
                    continue
            except OSError:
                pass
            if time.time() > end:
                raise TimeoutError(f"{path} held for {wait:.0f}s; delete it if no verify.py is running")
            time.sleep(0.005)
    try:
        yield
    finally:
        try:
            retry(lambda: os.remove(path))
        except OSError:
            pass


def merge_state(disk, base, mine, owned):
    """Three-way merge of one save: keys this process left as loaded keep the disk value."""
    out = dict(disk)
    for k in set(base) | set(mine):
        if k in ("forged", "seal") or not owned(k):
            continue
        if k not in mine:
            out.pop(k, None)  # this process removed it
        elif k in base and mine[k] == base[k]:
            continue
        elif k in ("failures", "verified_by", "swarm", "receipt_trees") and isinstance(mine[k], dict):
            out[k] = merge_state(disk.get(k) or {}, base.get(k) or {}, mine[k], lambda _: True)
        elif k in ("rebaselines", "loosened_reviewed") and isinstance(mine[k], list):
            have = list(disk.get(k) or [])
            out[k] = have + [r for r in mine[k] if r not in have]
        else:
            out[k] = mine[k]
    return out


def write_state_file(path, base, mine, owned):
    disk = read_state_file(path)
    out = merge_state(disk, base, mine, owned)
    if disk.get("forged"):
        out["forged"] = True
    if not out and not os.path.exists(path):
        return
    out["seal"] = seal_of(out)
    fd, tmp = tempfile.mkstemp(prefix=".verify-state.", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
        retry(lambda: os.replace(tmp, path))
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise
    out.pop("seal")
    _loaded[path] = json.loads(json.dumps(out))


def save_state(repo, state):
    shared_path, own_path = state_paths(repo)
    with state_lock(repo):
        if own_path == shared_path:
            write_state_file(shared_path, _loaded.get(shared_path, {}), state, lambda _: True)
            return
        write_state_file(shared_path, _loaded.get(shared_path, {}),
                         {k: state[k] for k in SHARED_KEYS if k in state}, lambda k: k in SHARED_KEYS)
        write_state_file(own_path, _loaded.get(own_path, {}),
                         {k: v for k, v in state.items() if k not in SHARED_KEYS},
                         lambda k: k not in SHARED_KEYS)


def git_common_dir(repo):
    """The repository's shared .git directory (the same for every worktree), or None outside Git.
    Read from disk, not from `git rev-parse`, so the inner loop spawns no process for it."""
    here = os.path.abspath(repo)
    while True:
        dot = os.path.join(here, ".git")
        if os.path.isdir(dot):
            return dot
        if os.path.isfile(dot):
            try:
                with open(dot, encoding="utf-8") as fh:
                    line = fh.read().strip()
            except OSError:
                return None
            if not line.startswith("gitdir:"):
                return None
            gitdir = os.path.normpath(os.path.join(here, line[len("gitdir:"):].strip()))
            try:
                with open(os.path.join(gitdir, "commondir"), encoding="utf-8") as fh:
                    return os.path.normpath(os.path.join(gitdir, fh.read().strip()))
            except OSError:
                return gitdir
        parent = os.path.dirname(here)
        if parent == here:
            return None
        here = parent


def cache_dir(repo):
    """Where caches live: under VERIFY_STATE_DIR when set; else inside Git's common directory, so
    every worktree of a repo shares them; else .verify-state-cache/ in the repo (left out of
    signatures and copies like the state files)."""
    home = outside_home(repo)
    if home:
        return os.path.join(home, "cache")
    common = git_common_dir(repo)
    return os.path.join(common, "verify-loop") if common else os.path.join(repo, ".verify-state-cache")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path, data):
    """Replace the file whole, so a reader never sees half of it."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".verify-state.", suffix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, separators=(",", ":"), sort_keys=True)
        retry(lambda: os.replace(tmp, path))
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def tree_files(repo):
    """(relative path, stat) for every file outside TREE_SKIP and the state files, in a fixed order."""
    out = []

    def walk(d, prefix):
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name)
        except OSError:
            return
        subdirs = []
        for e in entries:
            try:
                if e.is_dir():
                    if not e.is_symlink() and e.name not in TREE_SKIP and not is_state_file(e.name):
                        subdirs.append(e)
                elif e.name != ".git" and not is_state_file(e.name) and not e.name.endswith(".pyc"):
                    out.append((prefix + e.name, e.stat()))
            except OSError:
                continue
        for e in subdirs:
            walk(e.path, prefix + e.name + "/")

    walk(repo, "")
    return out


RACY = 2.0  # seconds: a file modified this recently may change again within one timestamp tick
TREE_INFO = {}  # what the last tree_sig call did: mode, files, hashed (shown by run --json)


def tree_sig(repo, fast=False):
    """Content signature of every file outside TREE_SKIP.

    Full (the default, and what --strict, status, ci and challenge use) reads every byte, so
    preserved timestamps cannot hide an edit. fast=True (non-strict runs and watch) reuses a file's
    content hash while its size, mtime and (on POSIX) ctime match the last time it was hashed, as
    git's index does: an edit that restores all of them goes unseen until a full pass. Both give
    the same signature when the stat data is honest, so status can judge a fast-recorded run."""
    path = os.path.join(cache_dir(repo), f"tree-{sha(os.path.realpath(repo))}.json")
    old = read_json(path)
    new, now, hashed = {}, time.time(), 0
    h = hashlib.sha256()
    files = tree_files(repo)
    for rel, st in files:
        stamp = [st.st_size, st.st_mtime_ns, st.st_ctime_ns if os.name != "nt" else 0]
        entry = old.get(rel)
        if fast and isinstance(entry, list) and entry[:3] == stamp:
            digest = entry[3]
        else:
            try:
                fh_hash = hashlib.sha256()
                with open(os.path.join(repo, rel), "rb") as fh:
                    for chunk in iter(lambda: fh.read(65536), b""):
                        fh_hash.update(chunk)
            except OSError:
                continue
            digest, hashed = fh_hash.hexdigest()[:32], hashed + 1
        if now - st.st_mtime > RACY:
            new[rel] = stamp + [digest]
        h.update(rel.encode("utf-8", "replace") + b"\0" + digest.encode() + b"\0")
    if new != old:
        try:
            write_json(path, new)
        except OSError:
            pass  # a cache that cannot be written only costs speed
    TREE_INFO.clear()
    TREE_INFO.update(mode="fast" if fast else "full", files=len(files), hashed=hashed)
    return h.hexdigest()[:16]


# ---- shared result cache ------------------------------------------------------------------
# A pass is a fact about one command on one tree. Any agent or worktree that runs the same command
# on the same content reuses it instead of running it again. Only passes are kept, only from runs
# whose tree did not move while they ran, and a pass recorded under the fast signature never serves
# a strict run: strict reuses only passes keyed by a full, every-byte signature.
CACHE_MAX = 1000


def result_key(cmd, tree):
    return sha("\0".join((cmd, tree, sys.platform)))


def cached_passes(repo, cmds, tree, strict):
    """{command: cache entry} for the commands with a reusable pass on this tree."""
    entries = read_json(os.path.join(cache_dir(repo), "results.json"))
    hits = {}
    for cmd in cmds:
        e = entries.get(result_key(cmd, tree))
        if isinstance(e, dict) and e.get("cmd") == cmd and e.get("tree") == tree and (e.get("full") or not strict):
            hits[cmd] = e
    return hits


def remember_passes(repo, passes, tree, full):
    """Record passes ({command: (output, seconds)}) under the lock, keeping the newest CACHE_MAX."""
    if not passes:
        return
    folder = cache_dir(repo)
    path, at = os.path.join(folder, "results.json"), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        os.makedirs(folder, exist_ok=True)
        with file_lock(os.path.join(folder, "results.lock")):
            entries = read_json(path)
            for cmd, (out, secs) in passes.items():
                key = result_key(cmd, tree)
                if (entries.get(key) or {}).get("full") and not full:
                    continue  # never downgrade a full-signature pass
                entries[key] = {"cmd": cmd, "tree": tree, "full": full, "at": at, "agent": agent_name(),
                                "seconds": round(secs, 3), "output": out[-2000:]}
            if len(entries) > CACHE_MAX:
                keep = sorted(entries, key=lambda k: str(entries[k].get("at")))[-CACHE_MAX:]
                entries = {k: entries[k] for k in keep}
            write_json(path, entries)
    except (OSError, TimeoutError):
        pass  # a cache that cannot be written only costs speed


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
    hashes[RECIPE + " require"] = sha(json.dumps(requirements(recipe_text)))
    if any(f["fresh"] is not None for f in features):  # absent key: older baselines keep their signature
        hashes[RECIPE + " fresh"] = sha(json.dumps([(f["name"], f["fresh"]) for f in features]))
    return hashes


def tampered(repo, state):
    base = state.get("baseline") or {}
    if not base:
        return []
    cur = check_hashes(repo)
    return sorted(k for k in base if cur.get(k) != base[k])


HARNESS_FAILURE = re.compile(r"ModuleNotFoundError|ImportError|FileNotFoundError|SyntaxError|missing dependency|command not found|not recognized as|can\'t open file|Failed to locate '|^\S*sh: \d+: \S+: not found", re.I | re.M)
# The shell, zsh, dash, the macOS xcode-select stub and Windows each say "no `python`" differently.
MISSING_PYTHON = re.compile(r"^(?:\S*sh: (?:line )?(?:\d+: )?)?python: (?:command )?not found|command not found: python\b|"
                            r"Failed to locate 'python'|'python' is not recognized", re.I | re.M)


def current_receipts(state, signature):
    """Failure receipts for the current checks, with a caught challenge's mutated run folded in.
    Each receipt's `files` (the file hashes when it went red) is looked up from its run's tree."""
    trees = state.get("receipt_trees") or {}
    receipts = {k: dict(r, files=trees.get(r["files_id"])) if isinstance(r, dict) and r.get("files_id") else r
                for k, r in (state.get("failures") or {}).items()}
    challenge = state.get("challenge", {})
    if challenge.get("verdict") == "caught" and challenge.get("check_signature") == signature:
        for key, row in challenge.get("mutated", {}).get("checks", {}).items():
            if key.startswith(challenge.get("feature", "") + "|") and not row.get("ok") and row.get("exit") is not None:
                receipts[key] = {"signature": signature, "exit": row["exit"], "output": row["output"],
                                 "mutation": challenge.get("mutation")}
    return receipts


def proven_by(feature, receipts, signature, passing=None, where=None):
    """The receipt that proves this feature's checks can go red: (command, signal, receipt) or None.
    It must belong to the current checks, contain a declared fail-signal that names a behavior, not
    be a harness error, not match a signal that the same check also prints when it passes, and
    (with `where`, see proof_where) have gone red on a wrong product, not on the environment."""
    for kind, cmd in feature["checks"]:
        if kind in ("lint", "type", "types"):
            continue
        key = f"{feature['name']}|{cmd}"
        r = receipts.get(key, {})
        out = r.get("output", "")
        if r.get("signature") != signature or HARNESS_FAILURE.search(out):
            continue
        pass_out = (passing or {}).get(key) or ""
        if where and where(feature, key, r):
            continue
        for signal in feature["signals"]:
            if signal in out and signal not in pass_out and not gates.weak_signal(signal):
                return cmd, signal, r
    return None


def proof_where(repo, red=()):
    """`where` for proven_by: why a receipt's red did not come from a wrong product, or None.
    `red`: keys (feature|command) failing right now. Their receipt is the wrong state itself, not yet
    restored, so it is judged once the check passes again."""
    now = file_sigs(repo)
    try:
        frozen = set(check_hashes(repo))
    except (OSError, ValueError):
        frozen = set()
    red = red if isinstance(red, set) else set(red)  # a live set: run_checks adds to it as checks fail
    return lambda feature, key, receipt: None if key in red else \
        gates.where_problem(sys.modules[__name__], repo, feature, receipt, now, frozen)


def red_keys(state):
    return {k for k, r in (state.get("checks") or {}).items() if isinstance(r, dict) and not r.get("ok")}


def where_reason(feature, receipts, where):
    """The first reason `where` gives for one of this feature's receipts."""
    for k, r in receipts.items():
        if k.startswith(feature["name"] + "|"):
            why = where(feature, k, r)
            if why:
                return why
    return None


def gate_findings_loosened(repo, features, state):
    """Weakenings of mapped test files a person has not reviewed (see gates.loosened)."""
    commands = [c for f in features for _, c in f["checks"]]
    tests = [t for t in find_tests(repo) if is_covered(t, commands, repo)]
    reviewed = set(state.get("loosened_reviewed") or [])
    return [x for x in gates.loosened(sys.modules[__name__], repo, tests) if x["id"] not in reviewed]


def gate_findings(repo, features, blind, state, where=None):
    """What the gates find on the current tree: {weak_signal, unmapped, loosened, proof_where}.
    Each is a list of lines; every one of them keeps `run --strict` red."""
    me = sys.modules[__name__]
    weak = [f"{f['name']}: `{s}` {gates.weak_signal(s)}" for f in features for s in f["signals"]
            if gates.weak_signal(s)]
    unmapped = gates.unmapped(me, repo, features, blind)
    loose = gate_findings_loosened(repo, features, state)
    try:
        signature = sha(json.dumps(check_hashes(repo), sort_keys=True))
    except (OSError, ValueError):
        signature = None
    receipts = current_receipts(state, signature) if signature else {}
    where = where or proof_where(repo, red_keys(state))
    bad_where = []
    for f in features:
        if not f["checks"] or not f["proofs"] or not signature:
            continue
        if proven_by(f, receipts, signature) and not proven_by(f, receipts, signature, where=where):
            bad_where.append(f"{f['name']}: {where_reason(f, receipts, where)}")
    return {"weak_signal": weak, "unmapped": unmapped, "loosened": loose, "proof_where": bad_where}


def not_independent(state, features, runner, signature=None, tree=None):
    """Checks whose freezer is not shown to differ from `runner` (or from an agent in `verified_by`
    that already proved the check on the same signature and tree): [(feature, kind, command, freezer)]."""
    frozen = state.get("frozen_by") or {}
    verified = state.get("verified_by") or {}
    out = []
    for f in features:
        for kind, cmd in f["checks"]:
            ckey = f"{f['name']}|{kind}|{cmd}"
            who = frozen.get(ckey)
            if not runner or not who:
                out.append((f["name"], kind, cmd, who))
            elif runner == who:
                v = verified.get(ckey) or {}
                if not (v.get("agent") not in (None, who) and signature and v.get("signature") == signature
                        and tree and v.get("tree") == tree):
                    out.append((f["name"], kind, cmd, who))
    return out


NOISE = re.compile(r"\S*[\\/](?:tmp|temp)[\\/]\S*|/tmp/\S+|0x[0-9a-f]+|\d+(?:\.\d+)?s\b|\d{2}:\d{2}:\d{2}", re.I)


def fingerprint(cmd, out):
    """The failure with its noise (timings, temp paths, addresses) removed, so 'the same' is comparable."""
    tail = "\n".join(out.rstrip().splitlines()[-TAIL_LINES:])
    return sha(cmd + "\0" + NOISE.sub("", tail))


def track(repo, results, only, budget, failures, strict=False, signature=None, tree=None):
    """Compare this run to the last one and save it. (lines to print, True if the run must fail)."""
    if only:
        return ["note  --only run: loop state not updated (only a whole run can be compared)"], False
    state = load_state(repo)
    prev, checks, lines = state.get("checks", {}), {}, []
    receipts = state.setdefault("failures", {})
    if results and signature is None:
        signature = sha(json.dumps(check_hashes(repo), sort_keys=True))
    # The files as they were when a check went red, stored once per run and shared by its receipts.
    files_now = file_sigs(repo) if any(not ok for *_, ok, _, _ in results) else None
    files_id = sha(json.dumps(files_now, sort_keys=True)) if files_now is not None else None
    trees = state.setdefault("receipt_trees", {})
    if files_id:
        trees[files_id] = files_now
    for feat, kind, cmd, ok, out, code in results:
        key = f"{feat}|{cmd}"
        p = prev.get(key, {})
        fp = None if ok else fingerprint(cmd, out)
        count = (p.get("count", 0) + 1) if (not ok and p.get("fp") == fp) else (0 if ok else 1)
        checks[key] = {"ok": ok, "fp": fp, "count": count, "exit": code, "output": out[-4000:]}
        if not ok and code is not None and out.strip():
            receipts[key] = {"signature": signature, "exit": code, "output": out[-4000:], "agent": agent_name(),
                             "files_id": files_id}
        if p.get("ok") and not ok:
            lines.append(f"NEWLY RED  {feat} ({kind}): it passed last run, so the last change broke it")
        elif p and not p.get("ok") and ok:
            lines.append(f"NEWLY GREEN  {feat} ({kind})")
        if count >= 2:
            lines.append(f"SAME FAILURE x{count}  {feat} ({kind}): the same output again. Your picture of the "
                         "system is wrong; re-read the code and this output before another try")
    used = {r.get("files_id") for r in receipts.values() if isinstance(r, dict)}
    state["receipt_trees"] = {k: t for k, t in trees.items() if k in used}
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
                     "restore it, or have a person review it and run `verify.py baseline --reviewed-by <name> --reason <why>`")
    if state.get("forged"):
        lines.append(f"STATE FORGED  {STATE} was edited outside verify.py. Its history cannot be trusted: "
                     "delete it and verify again from scratch")
    red = bool(failures or changed or strays or state.get("forged"))
    rounds = state.get("rounds", 0) + 1 if red else 0
    if red and rounds >= budget:
        lines.append(f"BUDGET  {rounds} red runs in a row (budget {budget}): stop, report what passes, "
                     "what fails and what you would try next")
    state.update({"checks": checks, "rounds": rounds, "result": "red" if red else "green",
                  "strict": strict, "tree": tree or tree_sig(repo, fast=not strict)})
    save_state(repo, state)
    return lines, bool(changed or strays or state.get("forged"))


def file_sigs(repo):
    """{relative path: content hash} for every file outside SKIP_DIRS: what `scope` compares against."""
    sigs = {}
    for root, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not is_state_file(d))
        for f in sorted(files):
            if is_state_file(f) or f.endswith(".pyc"):
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


def frozen_lines(repo):
    """What a re-baseline compares line by line: each check command, each feature's signals and
    `fresh:` runs, and the recipe's `require:` words."""
    text = read(repo, RECIPE)
    features, _ = parse(text, repo=repo)
    return {"checks": sorted(f"{f['name']}|{k}|{c}" for f in features for k, c in f["checks"]),
            "signals": {f["name"]: f["signals"] for f in features}, "require": requirements(text),
            "fresh": {f["name"]: fresh_count(f["fresh"])[0] for f in features if f["fresh"] is not None}}


def weakened(repo, state, hashes, lines):
    """Frozen checks a re-baseline would change or drop. Additions are not listed: a new check, test
    file, oracle or feature only adds to the proof, and neither does a ## Run repair. Include files
    are judged by the checks parsed from them, so adding a feature there is an addition too."""
    base = state.get("baseline") or {}
    old = state.get("baseline_lines")
    includes = {os.path.normpath(i).replace("\\", "/") for i in find_includes(read(repo, RECIPE))}
    skip = {RECIPE + " run"} | includes | ({RECIPE + " checks", RECIPE + " signals"} if old else set()) \
        | ({RECIPE + " require"} if old and "require" in old else set())         | ({RECIPE + " fresh"} if old and "fresh" in old else set())
    out = [k for k in sorted(base) if k not in skip and hashes.get(k) != base[k]]
    if old:
        out += [f"check removed or edited: {c}" for c in old.get("checks", []) if c not in lines["checks"]]
        out += [f"fail-signal changed: {name}" for name, sig in sorted(old.get("signals", {}).items())
                if name in lines["signals"] and lines["signals"][name] != sig]
        out += [f"requirement removed: require: {w}" for w in old.get("require", []) if w not in lines["require"]]
        out += [f"fresh runs cut: {name} (fresh: {n} -> {lines['fresh'].get(name, 0)})"
                for name, n in sorted(old.get("fresh", {}).items()) if lines["fresh"].get(name, 0) < n]
    return out


def git_head(repo):
    try:
        p = subprocess.run(["git", "-C", repo, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def cmd_baseline(repo, reviewed_by=None, reason=None):
    if not os.path.isfile(os.path.join(repo, RECIPE)):
        print(f"no {RECIPE} in {repo}. Run `verify.py init` first.")
        return 2
    state = load_state(repo)
    try:
        hashes = check_hashes(repo)
    except (OSError, ValueError) as exc:
        print(f"invalid oracle: {exc}")
        return 2
    lines = frozen_lines(repo)
    changed = weakened(repo, state, hashes, lines)
    features, _ = parse(read(repo, RECIPE), repo=repo)
    loose = gate_findings_loosened(repo, features, state)
    changed += [f"loosened: {gates.loosened_text(x)}" for x in loose]
    if changed and not (reviewed_by and reviewed_by.strip() and reason and reason.strip()):
        for c in changed:
            print(f"BASELINE REFUSED  {c}")
        print("A frozen check changed or a test was loosened. The loop changes code, never the check: restore it, or have a "
              "person review the change and run `verify.py baseline --reviewed-by <name> --reason <why>`. "
              "Never pass --reviewed-by for a review that did not happen.")
        return 1
    if changed:
        state.setdefault("rebaselines", []).append({
            "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "by": reviewed_by.strip(),
            "reason": reason.strip(), "changed": changed, "head": git_head(repo)})
        if loose:
            state["loosened_reviewed"] = sorted(set(state.get("loosened_reviewed") or []) | {x["id"] for x in loose})
        print(f"RE-BASELINED  {len(changed)} frozen check change(s), reviewed by {reviewed_by.strip()}: "
              f"{reason.strip()}. `status` and `report` show this until it is committed.")
    # Who froze each check: kept for a check already frozen, the current agent for a new one.
    before = set((state.get("baseline_lines") or {}).get("checks", []))
    frozen_by = state.get("frozen_by") or {}
    state["frozen_by"] = {c: frozen_by[c] if c in before and frozen_by.get(c) else agent_name()
                          for c in lines["checks"]}
    state["baseline"], state["baseline_lines"] = hashes, lines
    state["baseline_files"] = file_sigs(repo)  # what a later session diffs to see what changed since
    save_state(repo, state)
    print(f"baseline recorded: {len(state['baseline'])} check file(s). From here an edit to any of "
          "them fails the run until a person reviews it and re-baselines.")
    return 0


def open_rebaselines(repo, state):
    """Re-baselines not yet committed: recorded at the current HEAD (or outside Git)."""
    head = git_head(repo)
    return [r for r in state.get("rebaselines", []) if r.get("head") == head]


def rebaseline_text(r):
    return f"{'; '.join(r['changed'])} (reviewed by {r['by']}: {r['reason']})"


def status_verdict(repo, state=None):
    """(state, detail, exit). Single decision path for text and --json output."""
    if not os.path.isfile(os.path.join(repo, RECIPE)):
        return "none", "no VERIFY.md; this repo does not use verify-loop", 0
    state = load_state(repo) if state is None else state
    if state.get("forged"):
        return "tampered", f"{STATE} was edited outside verify.py; delete it and verify again", 1
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
    if as_json:
        a = answer(repo)
        print(json.dumps(a, indent=2))
        return a["exit"]
    name, detail, code = status_verdict(repo)
    if name == "none":
        return 0
    print(f"VERIFY-STATE: {name}" + (f" ({detail})" if detail else ""))
    for r in open_rebaselines(repo, load_state(repo)):
        print(f"RE-BASELINED  {rebaseline_text(r)}")
    return code


VERDICTS = {"green": "green", "red": "red", "tampered": "red", "out-of-scope": "red",
            "partial": "partial", "stale": "stale", "never-run": "unverified", "none": "unverified"}


def answer(repo):
    """The one answer every caller gets (see references/answer.md): verdict, the VERIFY: line,
    observed rejections, what passed and the gaps, plus the status fields it is built from."""
    name, detail, code = status_verdict(repo)
    state = load_state(repo) if name != "none" else {}
    checks = state.get("checks", {}) or {}
    challenge = state.get("challenge") or {}
    features, blind = parse(read(repo, RECIPE), repo=repo) if name != "none" else ([], [])
    try:
        signature = sha(json.dumps(check_hashes(repo), sort_keys=True)) if features else None
    except (OSError, ValueError):
        signature = None
    receipts = current_receipts(state, signature) if signature else {}
    passing_out = {k: r.get("output", "") for k, r in checks.items() if isinstance(r, dict) and r.get("ok")}
    where = proof_where(repo, red_keys(state)) if features else None
    found = gate_findings(repo, features, blind, state, where) if features else \
        {"weak_signal": [], "unmapped": [], "loosened": [], "proof_where": []}
    rejections, unproven, unverified = [], [], []
    for f in features:
        if not f["checks"]:
            unverified.append(f["name"])
            continue
        hit = proven_by(f, receipts, signature, passing_out, where)
        if not hit or not f["proofs"]:
            unproven.append(f["name"])
            continue
        cmd, signal, r = hit
        line = next((ln.strip() for ln in reversed(r.get("output", "").splitlines()) if signal in ln), signal)
        rejections.append({"feature": f["name"], "command": cmd, "wrong_state": f["proofs"][0],
                           "fail_signal": signal, "exit": r.get("exit"), "observed": line[:300]})
    failing = sorted(k for k, r in checks.items() if isinstance(r, dict) and not r.get("ok"))
    blocked = [f"{k}: {why}" for k in failing
               for why in [gates.blocked(sys.modules[__name__], checks[k].get("output", ""), checks[k].get("exit"))] if why]
    passed = [{"feature": k.split("|", 1)[0], "command": k.split("|", 1)[1]}
              for k, r in sorted(checks.items()) if isinstance(r, dict) and r.get("ok") and "|" in k]
    orphans = [t for t in find_tests(repo) if not is_covered(t, [c for f in features for _, c in f["checks"]], repo)] \
        if features else []
    unchallenged = ["no caught challenge mutation for the current checks"] if features and \
        "challenge" in requirements(read(repo, RECIPE)) and not any(
            r.get("mutation") and r.get("signature") == signature for r in receipts.values()) else []
    dependent = [f"{feat} ({kind} `{cmd}`): frozen by {who or 'an unnamed agent'}"
                 for feat, kind, cmd, who in not_independent(state, features, agent_name(), signature, state.get("tree"))] \
        if features and "independent" in requirements(read(repo, RECIPE)) else []
    survey = state.get("survey") or {}
    current = survey.get("tree") == tree_sig(repo)
    survived = list(survey.get("items") or []) if current else []
    surveyed = [{"feature": k, "caught": c, "decided": d}
                for k, (c, d) in sorted((survey.get("caught") or {}).items())] if current else []
    todo, advice = [], None
    if features:
        from swarm import advise, swarm_items
        items = swarm_items(sys.modules[__name__], repo, state, where=where)
        todo = [{"feature": i["feature"], "action": i["action"], "detail": i["detail"], "next": i["next"]}
                for i in items if i["action"] != "done"]
        advice = advise(items)
    return {
        "verdict": VERDICTS[name], "state": name, "detail": detail, "exit": code,
        "next": todo, "swarm": advice,
        "verify_line": state.get("verify_line"),
        "rejections": rejections, "passed": passed, "surveyed": surveyed,
        "gaps": {"failing": failing, "unverified": unverified, "unproven": unproven,
                 "orphan_tests": orphans, "unchallenged": unchallenged, "not_independent": dependent,
                 "no_fresh": no_fresh_inputs(features, read(repo, RECIPE)) if features else [],
                 "blocked": blocked, "unmapped": found["unmapped"], "weak_signal": found["weak_signal"],
                 "proof_not_from_product": found["proof_where"],
                 "loosened": [gates.loosened_text(x) for x in found["loosened"]],
                 "blind_spots": blind, "survived": survived,
                 "rebaselined": [rebaseline_text(r) for r in open_rebaselines(repo, state)]},
        "rebaselines": state.get("rebaselines", []),
        "strict": bool(state.get("strict")), "rounds": state.get("rounds", 0),
        "failing": failing, "checks": len(checks), "receipts": sorted((state.get("failures") or {}).keys()),
        "challenge": {"feature": challenge.get("feature"), "verdict": challenge.get("verdict")}
        if challenge else None,
        "surveys": current_surveys(repo, signature),
    }


def current_surveys(repo, signature):
    """`challenge --auto` scores taken on the current checks and tree. A lead, not a receipt: the
    mutants come from the code, so they prove the checks notice changes, not that the code meets the spec."""
    surveys = read_json(os.path.join(cache_dir(repo), "surveys.json"))
    if not surveys or not signature:
        return {}
    tree = tree_sig(repo)
    return {f: {k: s[k] for k in ("files", "caught", "survived", "uncovered", "score", "at")}
            for f, s in sorted(surveys.items()) if s.get("signature") == signature and s.get("tree") == tree}


def orientation(repo, state=None):
    """What a session arriving at this repo needs before its first command: the recorded verdict,
    each feature's files and fail-proof receipt, what is frozen and what changed since it was frozen."""
    state = load_state(repo) if state is None else state
    name, detail, _ = status_verdict(repo, state)
    features, _ = parse(read(repo, RECIPE), repo=repo)
    try:
        signature = sha(json.dumps(check_hashes(repo), sort_keys=True))
    except (OSError, ValueError):
        signature = None
    proven = {k.split("|", 1)[0] for k, r in current_receipts(state, signature).items()
              if isinstance(r, dict) and r.get("signature") == signature} if signature else set()
    files, changed = state.get("baseline_files"), None
    if isinstance(files, dict):
        now = file_sigs(repo)
        changed = sorted(k for k in set(files) | set(now) if files.get(k) != now.get(k))
    # The baseline also freezes VERIFY.md's own sections (`VERIFY.md checks`, ...); name the files.
    frozen = sorted({k.split(" ", 1)[0] if k.startswith(RECIPE + " ") else k for k in state.get("baseline") or {}})
    return {"state": name, "detail": detail, "frozen": frozen,
            "features": [{"name": f["name"], "paths": f["paths"], "receipt": f["name"] in proven}
                         for f in features],
            "changed_since_baseline": changed}


def print_orientation(o):
    n = o["frozen"]
    frozen = f"frozen: {', '.join(n[:4])}" + (" ..." if len(n) > 4 else "") if n else "not frozen"
    head = "no recorded run" if o["state"] == "never-run" else \
        f"recorded state {o['state']}" + (f" ({o['detail']})" if o["detail"] else "")
    holds = "; the recorded proof holds, no re-run needed" if o["state"] == "green" else ""
    print(f"ORIENT: {head} | {frozen}{holds}")
    for f in o["features"]:
        receipt = "fail-proof receipt for the current checks" if f["receipt"] else "no fail-proof receipt"
        print(f"ORIENT  {f['name']}: {', '.join(f['paths']) or 'no path:'} | {receipt}")
    changed = o["changed_since_baseline"]
    if changed:
        print(f"ORIENT  changed since baseline: {', '.join(changed[:8])}" + (" ..." if len(changed) > 8 else ""))


def in_assess_dir():
    """True when state lives in the default --assess temp folder, not where the repo keeps it."""
    root = os.environ.get("VERIFY_STATE_DIR", "").strip()
    return bool(root) and os.path.abspath(root) == os.path.abspath(assess_dir())


def follow_up(repo, cmd):
    """A command an agent can paste as it is: this helper's real path, on the same state."""
    where = " --assess" if in_assess_dir() else state_flag()
    return f'python "{os.path.abspath(__file__)}" {cmd} "{repo}"{where}'


def print_draft(repo, a):
    print("ANSWER DRAFT: replace each [[fill: ...]], keep every other line, save it outside the repo")
    print(gates.draft(a), end="")
    print(f"Then: {follow_up(repo, 'answer-check')} --answer <file>")


def cmd_report(repo, as_json=False, assess=False):
    """Print the caller answer: verdict first, then VERIFY:, rejections, passes and gaps, then the
    answer drafted from them. Exit as status. `assess` answers a read-only question, so it points at
    `advance` instead of at more commands, and starts no helper agents."""
    a = answer(repo)
    if as_json:
        print(json.dumps(a, indent=2))
        return a["exit"]
    detail = a["detail"]
    if assess and a["state"] == "partial":
        detail = "assess makes no strict run; `advance` makes it proven"
    print(f"VERDICT: {a['verdict']}" + (f" ({detail})" if detail else ""))
    print(a["verify_line"] or "VERIFY: no whole run recorded")
    for r in a["rejections"]:
        print(f"REJECTED  {r['feature']}: `{r['command']}` went red (exit {r['exit']}) on {r['wrong_state']}"
              f" | signal: {r['fail_signal']} | observed: {r['observed']}")
    seen = gates.survey_caught(a)
    if not a["rejections"] and seen:
        print(f"REJECTED  no fail-proof receipt for the current checks; this survey saw {seen}")
    elif not a["rejections"]:
        print("REJECTED  none observed for the current checks: "
              + ("no spec-backed rejection is recorded" if a["surveys"] else "nothing here is proven able to fail"))
    for feat, s in a["surveys"].items():
        decided = s["caught"] + s["survived"] + s["uncovered"]
        print(f"SURVEY  {feat}: {s['caught']}/{decided} generated mutants caught ({s['score']:.0%}), "
              f"{s['survived']} survived, {s['uncovered']} uncovered, on {', '.join(s['files'])}. The mutants come "
              "from the code, so this is a lead, not a receipt: it shows the checks notice changes, not that the "
              "code meets the spec")
    for p in a["passed"]:
        print(f"PASSED  {p['feature']}: `{p['command']}`")
    rows = gates.gap_rows(a)
    for label, item in rows:
        print(f"GAP  {label}: {item}")
    if not rows:
        print("GAP  none recorded; green covers mapped claims only, not features nobody mapped")
    for t in a["next"]:
        print(f"NEXT  {t['feature']} [{t['action']}]: {t['next']}")
    if a["swarm"] and not assess:
        s = a["swarm"]
        print(f"SWARM: {s['mode']} ({s['why']})")
        if s["judge"] and s["mode"] != "judge":
            print(f"SWARM: judge too ({', '.join(s['judge'])} need an agent that did not freeze them)")
    print_draft(repo, a)
    return a["exit"]


def cmd_answer_check(repo, path, as_json=False):
    """The answer an agent hands back, held to what the helper knows: it must state the verdict, claim
    nothing the verdict does not support, and name every gap `report` lists. Exit 0 ok, 1 not, 2 unreadable."""
    try:
        if path == "-":
            text = sys.stdin.read()
        else:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
    except OSError as exc:
        print(f"answer-check: cannot read {path}: {exc}")
        return 2
    a = answer(repo)
    problems = gates.check_answer(a, text)
    if as_json:
        print(json.dumps({"verdict": a["verdict"], "ok": not problems,
                          "problems": [{"kind": k, "detail": d, "fix": f} for k, d, f in problems],
                          "exit": 1 if problems else 0}, indent=2))
    else:
        for kind, detail, fix in problems:
            print(f"ANSWER {kind}  {detail}" + ("" if kind in ("NO VERDICT", "MISSING") else f": {fix}"))
        print(f"ANSWER-CHECK: {'ok' if not problems else 'rejected'} (verdict {a['verdict']}, "
              f"{len(problems)} problem(s)). " + ("" if not problems else
              "Fix the answer, not the state: every problem is listed, none is hidden behind another."))
        lines = [fix for kind, _, fix in problems if kind in ("NO VERDICT", "MISSING")]
        if lines:
            print("ADD THESE LINES as they are (or say the same in your own words):")
            print("\n".join(lines))
    return 1 if problems else 0


def cmd_assess(repo, timeout=120, limit=8, jobs=1):
    """One call answers "is this check, or this claim, any good?": a fresh whole run, a mutation
    survey of every passing feature with a `path:`, the report and the answer drafted from it. Its
    state lives outside the repo (main() sets it), so the repo is left as it was."""
    if not os.path.isfile(os.path.join(repo, RECIPE)):
        print(f"ASSESS: no {RECIPE} in {repo}. Write one section per claim: `## <Feature>`, `- path: <product "
              f"file>`, `- test: `<command>``, `- fail-signal: <words the failure prints>` (VERIFY_FORMAT.md). "
              "Say in your answer that you added it, then run assess again.")
        return 2
    # What the repo itself recorded, before this call's scratch run: the state a handoff left.
    print_orientation(orientation(repo, read_state_file(os.path.join(repo, STATE)) if in_assess_dir() else None))
    code = cmd_run(repo, None, timeout, strict=False, jobs=jobs, use_cache=False, record_coverage=True)
    if code == 2:
        return 2
    from mutate import cmd_auto
    features, _ = parse(read(repo, RECIPE), repo=repo)
    checks = load_state(repo).get("checks", {}) or {}
    cov = read_json(coverage_path(repo))
    found = []
    for f in features:
        ran = [checks.get(f"{f['name']}|{cmd}") for _, cmd in f["checks"]]
        if f["journey"] or not f["checks"] or not all(r and r.get("ok") for r in ran):
            continue  # a mutation of a red or unchecked feature tells nothing
        if f["paths"]:
            cmd_auto(sys.modules[__name__], repo, f["name"], None, timeout, limit, False, jobs, found=found)
            continue
        # No `path:`: the product is what its checks imported, as HOLLOW reads it.
        files = sorted({rel for _, c in f["checks"] for rel in (cov.get(f"{f['name']}|{c}") or {}).get("files", [])
                        if rel.endswith(".py") and not is_test_file(rel) and defines_function(repo, rel)})
        if not files:
            print(f"CHALLENGE-AUTO: skipped {f['name']!r}: no `path:` names its product file and its checks "
                  "imported none, so nothing was mutated. Add a `path:` to survey it.")
            continue
        print(f"CHALLENGE-AUTO: {f['name']!r} has no `path:`; surveying what its checks imported: {', '.join(files)}")
        for rel in files[:3]:
            cmd_auto(sys.modules[__name__], repo, f["name"], rel, timeout, limit, False, jobs, found=found)
    # Survivors go into the answer, so a copied draft cannot drop them and answer-check asks for them.
    # Catches go in too, so the draft does not say nothing went red after the survey saw it go red.
    caught = {}
    for r in found:
        c = caught.setdefault(r["feature"], [0, 0])
        c[0] += r["verdict"] == "caught"
        c[1] += 1
    state = load_state(repo)
    state["survey"] = {"tree": tree_sig(repo), "items": [
        f"{r['file']}:{r['line']} {r['before'].strip()} -> {r['after'].strip()} ({r['feature']}: {r['verdict']}, "
        "the check still passed)" for r in found if r["verdict"] != "caught"], "caught": caught}
    save_state(repo, state)
    print("--")
    return cmd_report(repo, assess=True)


def diagnose_failure(out, exit_code, check_name, state=None):
    """Diagnose a failure into ('harness-gap' | 'spec-drift' | 'product-gap', summary, recommended_action)."""
    if state and state.get("result") == "tampered":
        return ("spec-drift", "Baseline tampering detected (check commands or oracle files modified).",
                "Consult team or spec. If a person approves, run `verify.py baseline --reviewed-by <name> --reason <why>`.")
    if state and "CHECK CHANGED" in str(state.get("detail", "")):
        return ("spec-drift", "Test checks or oracle files differ from the baseline.",
                "Do NOT weaken check silently. After a person reviews it, run `verify.py baseline --reviewed-by <name> --reason <why>`.")

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
    if MISSING_PYTHON.search(out or "") and shutil.which("python3"):
        return ("harness-gap", "Environment / dependency error: `python` is not on PATH, but `python3` is. "
                "Activate a virtualenv (it provides `python`) or put a `python` wrapper on PATH; a symlink to "
                "macOS's /usr/bin/python3 stub does not work. Changing the check to `python3` is a check edit.",
                "Provide `python` in the environment. Do NOT modify product logic.")
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
                                     "Confirm changes with team/spec. If a person approves, run `verify.py baseline --reviewed-by <name> --reason <why>`.")
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


def cmd_scaffold_ui(repo, route="/", output_name="smoke_ui.py"):
    """Scaffold a visual/browser DOM probe script using Playwright or headless HTTP+DOM checks."""
    scripts_dir = os.path.join(repo, "scripts")
    evidence_dir = os.path.join(repo, ".verify-evidence")
    os.makedirs(scripts_dir, exist_ok=True)
    os.makedirs(evidence_dir, exist_ok=True)
    target = os.path.join(scripts_dir, output_name)
    if os.path.exists(target):
        print(f"SCAFFOLD-UI: target already exists at {target}; not overwriting.")
        return 1

    content = f'''#!/usr/bin/env python3
"""{output_name} — Visual / UI regression probe.
Checks DOM tree, response status, and captures visual artifacts into .verify-evidence/
"""
import argparse, json, os, sys, time, urllib.request

EVIDENCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".verify-evidence"))
os.makedirs(EVIDENCE_DIR, exist_ok=True)

def check_ui(base_url, route):
    url = base_url.rstrip("/") + route
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={{"User-Agent": "VerifyLoop-UIProbe/1.0"}})
        with urllib.request.urlopen(req, timeout=15) as resp:
            elapsed = time.time() - t0
            html = resp.read().decode("utf-8", errors="replace")
            status = resp.status
            # Basic sanity assertions
            has_body = "<body" in html.lower()
            has_error = "500 internal server error" in html.lower() or "unhandled exception" in html.lower()
            ok = status == 200 and has_body and not has_error
            evidence = {{
                "timestamp": time.time(),
                "route": route,
                "url": url,
                "status": status,
                "elapsed_sec": round(elapsed, 3),
                "has_body": has_body,
                "has_fatal_error": has_error,
                "html_bytes": len(html),
                "verdict": "green" if ok else "red"
            }}
            with open(os.path.join(EVIDENCE_DIR, "ui_probe_evidence.json"), "w", encoding="utf-8") as fh:
                json.dump(evidence, fh, indent=2)

            if ok:
                print(f"[UI OK] {{route}} ({{status}}, {{len(html)}} bytes, {{elapsed:.2f}}s)")
                return True
            else:
                print(f"[UI FAIL] {{route}} (status: {{status}}, has_body: {{has_body}}, error: {{has_error}})")
                return False
    except Exception as exc:
        print(f"[UI FAIL] {{route}} request error: {{exc}}")
        return False

def main():
    parser = argparse.ArgumentParser(description="UI / Web Route Verification Probe")
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--route", default="{route}")
    args = parser.parse_args()
    ok = check_ui(args.base_url, args.route)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
'''
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print(f"SCAFFOLD-UI: Generated UI route probe at scripts/{output_name}")
    print("Suggested addition to VERIFY.md:")
    print(f"  ## UI: Route {route}")
    print(f"  - run: `python scripts/{output_name} --route {route}`")
    print(f"  - fail-signal: [UI FAIL]")
    print(f"  - fail-proof: introduced server 500/syntax error on route, probe rejected, restored")
    return 0


def cmd_contract(repo, old_spec_path, new_spec_path, as_json=False):
    """Detect breaking changes and schema contract violations between two API/schema specs."""
    def load_spec(p):
        full = p if os.path.isabs(p) else os.path.join(repo, p)
        if not os.path.isfile(full):
            raise FileNotFoundError(f"Spec file not found: {p}")
        with open(full, encoding="utf-8") as fh:
            text = fh.read()
        try:
            return json.loads(text)
        except Exception:
            try:
                import yaml
                return yaml.safe_load(text)
            except Exception:
                raise ValueError(f"Cannot parse {p} as JSON or YAML")

    try:
        old_data = load_spec(old_spec_path)
        new_data = load_spec(new_spec_path)
    except Exception as exc:
        print(f"CONTRACT-ERROR: {exc}")
        return 2

    violations = []
    # Check OpenAPI breaking changes
    if isinstance(old_data, dict) and "paths" in old_data and isinstance(new_data, dict) and "paths" in new_data:
        old_paths = old_data["paths"]
        new_paths = new_data["paths"]
        for p, methods in old_paths.items():
            if p not in new_paths:
                violations.append(f"Removed endpoint path: {p}")
                continue
            if isinstance(methods, dict) and isinstance(new_paths[p], dict):
                for m in methods:
                    if m.lower() in ("get", "post", "put", "delete", "patch") and m not in new_paths[p]:
                        violations.append(f"Removed HTTP method {m.upper()} on endpoint {p}")

    # Check JSON Schema breaking changes
    if isinstance(old_data, dict) and ("properties" in old_data or "required" in old_data):
        old_req = set(old_data.get("required", []))
        new_req = set(new_data.get("required", [])) if isinstance(new_data, dict) else set()
        added_req = new_req - old_req
        if added_req:
            violations.append(f"Newly added required field(s) in schema: {', '.join(sorted(added_req))}")
        old_props = set(old_data.get("properties", {}).keys())
        new_props = set(new_data.get("properties", {}).keys()) if isinstance(new_data, dict) else set()
        removed_props = old_props - new_props
        if removed_props:
            violations.append(f"Removed property field(s) in schema: {', '.join(sorted(removed_props))}")

    ok = len(violations) == 0
    if as_json:
        report = {
            "verdict": "green" if ok else "red",
            "old_spec": old_spec_path,
            "new_spec": new_spec_path,
            "violations": violations,
            "exit": 0 if ok else 1
        }
        print(json.dumps(report, indent=2))
    else:
        if ok:
            print(f"CONTRACT-VERIFY: [GREEN] No breaking changes detected between {old_spec_path} and {new_spec_path}.")
        else:
            print(f"CONTRACT-VERIFY: [RED] Detected {len(violations)} backward-compatibility violation(s):")
            for v in violations:
                print(f"  - {v}")
    return 0 if ok else 1


def cmd_auto_loop(repo, target_files, max_iterations=5, timeout=120, strict=False):
    """Autonomous iterative verification loop with scope enforcement and budget guardrails."""
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        print(f"AUTO-LOOP: no {RECIPE} found in {repo}.")
        return 2

    # Step 1: Set scope if target files specified
    if target_files:
        code = cmd_scope(repo, target_files, add=False, clear=False, check=False)
        if code != 0:
            return code
        print(f"AUTO-LOOP: Scoped target files: {', '.join(target_files)}")

    print(f"AUTO-LOOP: Commencing autonomous verification cycle (budget: {max_iterations} iterations)...")
    for iteration in range(1, max_iterations + 1):
        print(f"\n--- [AUTO-LOOP Iteration {iteration}/{max_iterations}] ---")
        run_code = cmd_run(repo, only=None, timeout=timeout, strict=strict, budget=max_iterations, as_json=False)
        state = load_state(repo)
        verdict = state.get("result", "unknown")

        if run_code == 0 and verdict == "green":
            print(f"\nAUTO-LOOP: [STRICT GREEN] Verification succeeded on iteration {iteration}!")
            return 0

        # Run triage to diagnose the red state
        print(f"\n[AUTO-LOOP Iteration {iteration}] Run was red. Running triage...")
        cmd_triage(repo, as_json=False)

        # Check for guardrail trip conditions
        rounds = state.get("rounds", 0)
        checks = state.get("checks", {})
        has_same_failure = any(c.get("count", 1) >= 2 for c in checks.values() if isinstance(c, dict) and not c.get("ok"))
        if has_same_failure:
            print(f"AUTO-LOOP: Detected repeated identical failure (SAME FAILURE x2). Stopping to prevent churn.")
            return 1
        if rounds >= max_iterations:
            print(f"AUTO-LOOP: Exceeded run budget ({max_iterations} attempts). Stopping.")
            return 1

    print(f"AUTO-LOOP: Budget exhausted without green verdict.")
    return 1


def cmd_watch(repo, interval=2.0, max_runs=0):
    """Continuously poll repo for file changes and run affected checks."""
    path = os.path.join(repo, RECIPE)
    if not os.path.isfile(path):
        print(f"no {RECIPE} in {repo}. Run `verify.py init` to draft one.")
        return 2
    # Baseline first: a change made once "Watching" is printed is always seen.
    last_sig = tree_sig(repo, fast=True)
    print(f"Watching {repo} for changes (interval: {interval}s)... Press Ctrl+C to stop.", flush=True)
    runs_done = 0
    try:
        while True:
            time.sleep(interval)
            cur_sig = tree_sig(repo, fast=True)
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
    r.add_argument("--jobs", type=int, default=1,
                   help="run up to N checks at once; only for checks that share no app or files (default 1)")
    r.add_argument("--no-cache", action="store_true",
                   help="run every check even if an identical pass on this exact content is cached")
    r.add_argument("--record-coverage", action="store_true",
                   help="with coverage.py importable, record the repo files each check executes so "
                        "--affected can select by them")
    b = sub.add_parser("baseline", help="freeze the check files; later edits to them fail the run")
    b.add_argument("repo", nargs="?", default=".")
    b.add_argument("--reviewed-by", help="the person who reviewed a change to a frozen check")
    b.add_argument("--reason", help="why the reviewed check change is right (spec change, harness repair)")
    t = sub.add_parser("status", help="is the last run green and still true of the files? (exit 0/1/3)")
    t.add_argument("repo", nargs="?", default=".")
    t.add_argument("--json", action="store_true", help="print one JSON object (same exit codes)")
    ss = sub.add_parser("scaffold-skill", help="create mode: draft .claude/skills/verify/ + feature map from the stack")
    ss.add_argument("repo", nargs="?", default=".", help="repo root, or the touched package in a monorepo")
    ss.add_argument("--adopt", action="store_true",
                    help="keep an existing SKILL.md (e.g. one Claude Code's /verify recorded) and add what is missing")
    sk = sub.add_parser("skill-check", help="create mode: lint the project verify skill and its VERIFY.md links")
    sk.add_argument("repo", nargs="?", default=".")
    sk.add_argument("--json", action="store_true", help="print problems as JSON")
    mt = sub.add_parser("maintain", help="maintain mode: read-only audit of the verify skill vs VERIFY.md, proof and churn")
    mt.add_argument("repo", nargs="?", default=".")
    mt.add_argument("--since", help="git ref of the last pass (default: last-maintained: in features/README.md)")
    mt.add_argument("--json", action="store_true", help="print the audit as JSON")
    rp = sub.add_parser("report", help="the caller answer: verdict, VERIFY: line, rejections, passes, gaps")
    rp.add_argument("repo", nargs="?", default=".")
    rp.add_argument("--json", action="store_true", help="print the answer as JSON (same as status --json)")
    ac = sub.add_parser("answer-check", help="check a final answer against report: verdict stated, no "
                                             "overclaim, every gap named (exit 0 ok, 1 not)")
    ac.add_argument("repo", nargs="?", default=".")
    ac.add_argument("--answer", required=True, help="the answer file, or - for stdin")
    ac.add_argument("--json", action="store_true", help="print the problems as JSON")
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
    su = sub.add_parser("scaffold-ui", help="generate visual/web DOM route probe and evidence capture")
    su.add_argument("repo", nargs="?", default=".")
    su.add_argument("--route", default="/", help="frontend route or path to probe (default: /)")
    su.add_argument("--output", default="smoke_ui.py", help="target script name under scripts/ (default: smoke_ui.py)")
    so = sub.add_parser("scaffold-oracle", help="generate test driver and VERIFY.md feature from OpenAPI spec or JSON schema")
    so.add_argument("spec", help="path to OpenAPI (yaml/json) or JSON Schema file")
    so.add_argument("repo", nargs="?", default=".")
    so.add_argument("--type", choices=["auto", "openapi", "schema"], default="auto", help="specification type")
    ct = sub.add_parser("contract", help="verify schema / API backward-compatibility and breaking changes")
    ct.add_argument("old_spec", help="baseline specification file (OpenAPI or JSON Schema)")
    ct.add_argument("new_spec", help="updated specification file")
    ct.add_argument("repo", nargs="?", default=".")
    ct.add_argument("--json", action="store_true", help="output contract breaking changes as JSON")
    asx = sub.add_parser("assess", help="one read-only call: run, mutation survey, report and answer draft")
    asx.add_argument("repo", nargs="?", default=".")
    asx.add_argument("--timeout", type=int, default=120, help="seconds per check (default 120)")
    asx.add_argument("--max", type=int, default=8, help="most mutations per feature (default 8)")
    asx.add_argument("--jobs", type=int, default=1, help="parallel checks and mutations; only for isolated checks")
    adv = sub.add_parser("advance", help="execute bounded mechanical steps; yield decisions to an agent")
    adv.add_argument("repo", nargs="?", default=".")
    adv.add_argument("--max-steps", type=int, default=3, help="maximum automatic actions (default 3)")
    adv.add_argument("--timeout", type=int, default=120, help="seconds per check (default 120)")
    adv.add_argument("--jobs", type=int, default=1, help="parallel checks; use only for isolated checks")
    adv.add_argument("--refresh", action="store_true", help="rerun unchanged inputs after external environment changes")
    adv.add_argument("--json", action="store_true", help="print steps, pending tasks and the canonical report")
    lp = sub.add_parser("loop", help="autonomous iterative verification loop with scope enforcement and budget guardrails")
    lp.add_argument("repo", nargs="?", default=".")
    lp.add_argument("--scope", nargs="*", default=[], help="pin touched files/patterns for scope enforcement")
    lp.add_argument("--max", type=int, default=5, help="maximum iterations before halting (default: 5)")
    lp.add_argument("--timeout", type=int, default=120, help="seconds per check (default: 120)")
    lp.add_argument("--strict", action="store_true", help="require strict proof and receipts")
    w = sub.add_parser("watch", help="watch repo for changes and run affected checks continuously")
    w.add_argument("repo", nargs="?", default=".")
    w.add_argument("--interval", type=float, default=2.0, help="polling interval in seconds (default: 2.0)")
    w.add_argument("--max-runs", type=int, default=0, help="exit after N runs (default: 0 = run forever)")
    ch = sub.add_parser("challenge", help="challenge a feature check with one explicit mutation in scratch copies")
    ch.add_argument("repo", nargs="?", default=".")
    ch.add_argument("--feature", required=True, help="exact feature name in VERIFY.md")
    ch.add_argument("--mutation", help="JSON file with file, before, after and claim")
    ch.add_argument("--file", help="inline mutation target file (repo-relative), instead of --mutation JSON file")
    ch.add_argument("--before", help="inline mutation unique substring to replace")
    ch.add_argument("--after", help="inline mutation replacement string")
    ch.add_argument("--claim", help="inline mutation claim description (defaults to '<feature>: <before> -> <after>')")
    ch.add_argument("--auto", metavar="FILE", nargs="?", const="",
                    help="generate standard mutations for this product file; report a mutation score. "
                         "Without FILE: the feature's `path:` files, or with --diff every changed product file")
    ch.add_argument("--diff", metavar="REF", nargs="?", const="HEAD",
                    help="with --auto, mutate only lines changed since REF (default HEAD)")
    ch.add_argument("--max", type=int, default=20, help="most mutations to try with --auto (default 20)")
    ch.add_argument("--json", action="store_true", help="with --auto, print the score as JSON")
    ch.add_argument("--timeout", type=int, default=120, help="seconds per check")
    ch.add_argument("--jobs", type=int, default=1,
                    help="with --auto, judge mutations in N parallel scratch copies (default 1; "
                         "a ## Run recipe forces 1)")
    sw = sub.add_parser("swarm", help="coordinate multi-agent verification: work-stealing claims, independence routing, or repo-wide auto-challenge")
    sw.add_argument("repo", nargs="?", default=".")
    sw.add_argument("--claim", action="store_true", help="atomically claim the highest-priority task this agent is eligible for")
    sw.add_argument("--release", metavar="FEATURE", nargs="?", const="*", help="release a claimed feature (or '*' for all claims held by this agent)")
    sw.add_argument("--done", metavar="FEATURE", help="mark a claimed feature's current task step done and release its claim")
    sw.add_argument("--role", choices=["any", "worker", "judge"], default="any",
                    help="filter claimable tasks by role: worker (fix/prove/freeze/challenge) or judge (independent/challenge/run)")
    sw.add_argument("--lease", type=int, default=600, help="claim lease duration in seconds before another agent can steal it (default: 600)")
    sw.add_argument("--auto", action="store_true", help="run parallel mutation surveys across all mapped features and record receipts in the shared lane")
    sw.add_argument("--diff", metavar="REF", nargs="?", const="HEAD", help="with --auto, mutate only lines changed since REF (default HEAD)")
    sw.add_argument("--max", type=int, default=15, help="with --auto, max mutations per feature (default: 15)")
    sw.add_argument("--jobs", type=int, default=2, help="with --auto, parallel scratch workers per feature (default: 2)")
    sw.add_argument("--timeout", type=int, default=120, help="with --auto, seconds per check (default: 120)")
    sw.add_argument("--json", action="store_true", help="print swarm plan, claim, or auto survey as JSON")
    rv = sub.add_parser("review", help="review a change by proof: weakened tests/checks, unproven changed lines")
    rv.add_argument("repo", nargs="?", default=".")
    rv.add_argument("--base", default="HEAD", help="commit the change is measured from (default HEAD; a PR: its base)")
    rv.add_argument("--no-mutate", action="store_true", help="static findings only; skip the mutation survey")
    rv.add_argument("--max", type=int, default=20, help="most mutations per feature (default 20)")
    rv.add_argument("--jobs", type=int, default=1, help="parallel scratch lanes for the survey")
    rv.add_argument("--timeout", type=int, default=120, help="seconds per check")
    rv.add_argument("--json", action="store_true", help="print findings as JSON (same exit codes)")
    ci = sub.add_parser("ci", help="fresh proof from committed inputs; ignore local verification state")
    ci.add_argument("repo", nargs="?", default=".")
    ci.add_argument("--plan", required=True, help="committed repo-relative JSON feature/mutation list")
    ci.add_argument("--output", required=True, help="evidence directory outside the checkout")
    ci.add_argument("--timeout", type=int, default=120, help="seconds per check")
    for p in sub.choices.values():
        where = p.add_mutually_exclusive_group()
        where.add_argument("--assess", action="store_true",
                           help="read-only for the repo: keep state and caches in a temp folder "
                                "(VERIFY_STATE_DIR, else verify-loop-assess in the system temp dir)")
        where.add_argument("--state-dir", metavar="DIR",
                           help="keep state and caches under DIR instead of the repo (= VERIFY_STATE_DIR)")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)
    if a.cmd == "assess" and not a.state_dir:
        a.assess = True  # assess never writes to the repo
    if a.state_dir:
        os.environ["VERIFY_STATE_DIR"] = os.path.abspath(a.state_dir)
    elif a.assess:
        os.environ["VERIFY_STATE_DIR"] = os.environ.get("VERIFY_STATE_DIR", "").strip() or assess_dir()
    if a.assess:
        # The checks themselves should not leave bytecode or a pytest cache behind either.
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        if "no:cacheprovider" not in os.environ.get("PYTEST_ADDOPTS", ""):
            os.environ["PYTEST_ADDOPTS"] = (os.environ.get("PYTEST_ADDOPTS", "") + " -p no:cacheprovider").strip()
    try:
        agent_name()
    except ValueError as exc:
        print(f"verify.py: {exc}")
        sys.exit(2)
    if a.cmd == "assess":
        sys.exit(cmd_assess(repo, a.timeout, a.max, a.jobs))
    if a.cmd == "advance":
        from advance import cmd_advance
        sys.exit(cmd_advance(sys.modules[__name__], repo, a.max_steps, a.timeout, a.jobs, a.refresh, a.json))
    if a.cmd == "ci":
        from ci import cmd_ci
        sys.exit(cmd_ci(sys.modules[__name__], repo, a.plan, a.output, a.timeout))
    if a.cmd == "review":
        from review import cmd_review
        sys.exit(cmd_review(sys.modules[__name__], repo, a.base, not a.no_mutate, a.jobs, a.max, a.timeout, a.json))
    if a.cmd == "swarm":
        from swarm import cmd_swarm
        sys.exit(cmd_swarm(sys.modules[__name__], repo, claim=a.claim, release=a.release, done=a.done,
                           role=a.role, lease=a.lease, auto=a.auto, diff=a.diff, jobs=a.jobs,
                           limit=a.max, timeout=a.timeout, as_json=a.json))
    if a.cmd == "challenge":
        auto = a.auto is not None
        inline_parts = (a.file is not None, a.before is not None, a.after is not None)
        inline = any(inline_parts)
        if inline and not all(inline_parts):
            ap.error("inline challenge requires --file, --before, and --after together")
        if sum([bool(a.mutation), inline, auto]) != 1:
            ap.error("challenge needs exactly one of --mutation, (--file --before --after), or --auto")
        if a.diff and not auto:
            ap.error("--diff works with --auto")
        if auto:
            from mutate import cmd_auto
            sys.exit(cmd_auto(sys.modules[__name__], repo, a.feature, a.auto or None, a.timeout, a.max, a.json,
                              a.jobs, a.diff))
        from challenge import cmd_challenge
        mut_arg = {"file": a.file, "before": a.before, "after": a.after,
                   "claim": a.claim or f"{a.feature}: {a.before.strip()} -> {a.after.strip()}"} if inline else a.mutation
        sys.exit(cmd_challenge(sys.modules[__name__], repo, a.feature, mut_arg, a.timeout))
    if a.cmd == "scaffold-driver":
        sys.exit(cmd_scaffold_driver(repo, a.type))
    if a.cmd == "scaffold-ui":
        sys.exit(cmd_scaffold_ui(repo, a.route, a.output))
    if a.cmd == "scaffold-oracle":
        sys.exit(cmd_scaffold_oracle(repo, a.spec, a.type))
    if a.cmd == "contract":
        sys.exit(cmd_contract(repo, a.old_spec, a.new_spec, a.json))
    if a.cmd == "loop":
        sys.exit(cmd_auto_loop(repo, a.scope, a.max, a.timeout, a.strict))
    if a.cmd == "watch":
        sys.exit(cmd_watch(repo, a.interval, a.max_runs))
    if a.cmd == "scope":
        sys.exit(cmd_scope(repo, a.patterns, a.add, a.clear, a.check))
    if a.cmd == "init":
        sys.exit(cmd_init(repo))
    if a.cmd == "baseline":
        sys.exit(cmd_baseline(repo, a.reviewed_by, a.reason))
    if a.cmd == "status":
        sys.exit(cmd_status(repo, a.json))
    if a.cmd in ("scaffold-skill", "skill-check"):
        from create import cmd_scaffold_skill, cmd_skill_check
        if a.cmd == "scaffold-skill":
            sys.exit(cmd_scaffold_skill(sys.modules[__name__], repo, a.adopt))
        sys.exit(cmd_skill_check(sys.modules[__name__], repo, a.json))
    if a.cmd == "maintain":
        from maintain import cmd_maintain
        sys.exit(cmd_maintain(sys.modules[__name__], repo, a.since, a.json))
    if a.cmd == "report":
        sys.exit(cmd_report(repo, a.json))
    if a.cmd == "answer-check":
        sys.exit(cmd_answer_check(repo, a.answer, a.json))
    if a.cmd == "triage":
        sys.exit(cmd_triage(repo, a.json))
    if a.cmd == "tests":
        sys.exit(cmd_tests(repo, a.strict))
    sys.exit(cmd_run(repo, a.only, a.timeout, a.strict, a.budget, a.affected, a.stress, a.json, a.quarantine, a.jobs,
                     not a.no_cache, a.record_coverage))


if __name__ == "__main__":
    main()
