"""check-the-check: would this check catch a bug? Answers from runs, never from reading.

    python check.py <repo> --check "python -m unittest test_x" [--product FILE ...] [--base REF] [--json]

Every run happens in a scratch copy under the system temp folder; the repo is only read (git reads
included), so its `git status` is unchanged. Four probes, each printed as one verdict line:

  RUN        the check itself: pass or fail, which test functions ran
  NEVER RAN  a test function defined in a test file the check loaded, that never started
  HOLLOW     a product file the check imported but whose functions it never called
  SURVIVED   a one-line bug planted in a product file that the check still passed
  BASE       with --base: the check against the product as it was at REF. A test added since REF
             that passes there cannot catch what the change fixed

Python checks are measured (which tests started, which raised, which product lines ran) through
a sitecustomize put on PYTHONPATH; any other command still gets RUN, SURVIVED and BASE.
Exit: 0 strong, 1 weak, 2 the check fails now, 3 blocked (it could not run), 4 bad arguments.
"""
import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams  # noqa: E402

SKIP_COPY = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox"}
SUPPORT = re.compile(r"fixture|conftest|mock|fake|stub|factor(y|ies)|sitecustomize", re.I)  # test support, not product
SKIP_SCAN =SKIP_COPY | {"node_modules", "venv", ".venv", "dist", "build", "target", "vendor"}
TEST_FILE = re.compile(r"^(test_.+|.+_test)\.py$|^conftest\.py$|^.+\.(test|spec)\.(js|jsx|ts|tsx|mjs|cjs)$|^.+_test\.go$")
# Exit codes and output that mean the check never got to judge the product.
BLOCKED = re.compile(r"command not found|is not recognized as an internal or external command|"
                     r"No module named (pytest|unittest)\b|ModuleNotFoundError: No module named '(pytest|node)'|"
                     r"Address already in use|ECONNREFUSED|Could not resolve host", re.I)

# (name, pattern, replacement): one-line mutations, the first match on a line.
OPERATORS = [
    ("eq-to-ne", r"==", "!="),
    ("ne-to-eq", r"!=", "=="),
    ("le-to-lt", r"<=", "<"),
    ("ge-to-gt", r">=", ">"),
    ("lt-to-le", r"(?<![<=!-])<(?![<=])", "<="),
    ("gt-to-ge", r"(?<![>=-])>(?![>=])", ">="),
    ("and-to-or", r"\band\b|&&", lambda m: "or" if m.group(0) == "and" else "||"),
    ("or-to-and", r"\bor\b|\|\|", lambda m: "and" if m.group(0) == "or" else "&&"),
    ("true-to-false", r"\bTrue\b|\btrue\b", lambda m: "False" if m.group(0) == "True" else "false"),
    ("false-to-true", r"\bFalse\b|\bfalse\b", lambda m: "True" if m.group(0) == "False" else "true"),
    ("plus-to-minus", r"(?<=\s)\+(?=\s)", "-"),
    ("minus-to-plus", r"(?<=\s)-(?=\s)", "+"),
    ("mul-to-div", r"(?<=\s)\*(?=\s)", "/"),
    ("int-off-by-one", r"(?<![\w.])(\d+)(?![\w.])", lambda m: str(int(m.group(1)) + 1)),
    ("decimal-nudged", r"(?<![\w.])(\d+)\.(\d+)(?![\w.])",
     lambda m: f"{m.group(1)}.{int(m.group(2)) + 1:0{len(m.group(2))}d}"),
    ("not-dropped", r"\bnot\s+", ""),
    ("in-to-not-in", r"\bin\b(?!\s*\(|\s*\{|\s*\[)", "not in"),
    ("return-to-none", r"^\s*return\s+(?!None\b|$)(.+)$", lambda m: m.group(0).replace(m.group(1), "None")),
]
PER_LINE = 6  # matches mutated per operator per line
QUOTED = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')
COMMENT = re.compile(r"^\s*(#|//|\*|/\*)")
STRING_ONLY = re.compile(r"""^\s*(['"]).*\1,?\s*$""")

# Put on PYTHONPATH for every Python process the check starts. It records, per process, into
# CTC_OUT: S = a function started in a repo file, U = it ended by raising (a failed test), L = a
# product line ran. 3.12+ uses sys.monitoring (each location reports once, then costs nothing);
# older Pythons record starts only.
SITECUSTOMIZE = r'''import atexit, os, sys
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.environ.get("CTC_ROOT", "")
_out = os.environ.get("CTC_OUT", "")
_product = set(filter(None, os.environ.get("CTC_PRODUCT", "").split("|")))
_rows = set()
_rel = {}
def _where(fn):
    if fn in _rel:
        return _rel[fn]
    r = None
    if fn and not fn.startswith("<"):
        try:
            real = os.path.realpath(fn)
            rel = os.path.relpath(real, _root)
            if not rel.startswith("..") and os.path.dirname(real) != _here:
                r = rel.replace(os.sep, "/")
        except Exception:
            pass
    _rel[fn] = r
    return r
def _flush():
    try:
        with open(os.path.join(_out, "rec.%d" % os.getpid()), "a", encoding="utf-8") as fh:
            fh.write("".join(r + "\n" for r in _rows))
    except Exception:
        pass
if _root and _out:
    atexit.register(_flush)
    _mon = getattr(sys, "monitoring", None)
    try:
        E = _mon.events
        _mon.use_tool_id(5, "check-the-check")
        def _start(code, offset):
            try:
                rel = _where(code.co_filename)
                if rel:
                    _rows.add("F\t%s" % rel)
                    if code.co_flags & 0x2:
                        _rows.add("S\t%s\t%d\t%s" % (rel, code.co_firstlineno, getattr(code, "co_qualname", code.co_name)))
                    if rel in _product:
                        _mon.set_local_events(5, code, E.LINE)
            except Exception:
                pass
            return _mon.DISABLE
        def _line(code, line):
            _rows.add("L\t%s\t%d" % (_where(code.co_filename), line))
            return _mon.DISABLE
        def _unwind(code, offset, exc):  # global-only event: fires on every frame an exception leaves
            try:
                rel = _where(code.co_filename)
                if rel:
                    _rows.add("U\t%s\t%d" % (rel, code.co_firstlineno))
            except Exception:
                pass
        _mon.register_callback(5, E.PY_START, _start)
        _mon.register_callback(5, E.LINE, _line)
        _mon.register_callback(5, E.PY_UNWIND, _unwind)
        _mon.set_events(5, E.PY_START | E.PY_UNWIND)
        _rows.add("M\tlines")
    except Exception:
        def _prof(frame, event, arg):
            if event == "call":
                code = frame.f_code
                rel = _where(code.co_filename)
                if rel:
                    _rows.add("F\t%s" % rel)
                if rel and code.co_flags & 0x2:
                    _rows.add("S\t%s\t%d\t%s" % (rel, code.co_firstlineno, code.co_name))
        sys.setprofile(_prof)
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _here]
del sys.modules["sitecustomize"]
try:
    import sitecustomize
except ImportError:
    pass
'''


# ---------------------------------------------------------------- files

def rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def is_test(relpath):
    return bool(TEST_FILE.match(relpath.rsplit("/", 1)[-1])) or any(
        part in ("tests", "test") for part in relpath.split("/")[:-1])


def read(path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        return fh.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def copy_repo(repo, dest):
    """A scratch copy to run in. Heavy dependency folders are linked when the OS allows it."""
    os.makedirs(dest, exist_ok=True)
    for name in os.listdir(repo):
        if name in SKIP_COPY:
            continue
        src, dst = os.path.join(repo, name), os.path.join(dest, name)
        if name in ("node_modules", ".venv", "venv"):
            try:
                os.symlink(src, dst, target_is_directory=True)
                continue
            except OSError:
                pass
        if os.path.isdir(src):
            shutil.copytree(src, dst, symlinks=True, ignore=shutil.ignore_patterns(*SKIP_COPY))
        else:
            shutil.copy2(src, dst)
    return dest


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode:
        raise RuntimeError(p.stderr.strip() or f"git {' '.join(args)} failed")
    return p.stdout


def test_functions(path):
    """{(firstline, defline): qualname} for test functions a runner would collect: `test*`
    functions at module level or in a class."""
    try:
        tree = ast.parse(read(path))
    except (SyntaxError, ValueError, OSError):
        return {}
    out = {}

    def visit(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, prefix + child.name + ".")
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith("test"):
                first = min([child.lineno] + [d.lineno for d in child.decorator_list])
                out[(first, child.lineno)] = prefix + child.name
    visit(tree, "")
    return out


def defines_function(path):
    try:
        return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(ast.parse(read(path))))
    except (SyntaxError, ValueError, OSError):
        return False


def code_lines(path):
    """Line numbers that hold executable statements (for 'lines reached')."""
    try:
        tree = ast.parse(read(path))
    except (SyntaxError, ValueError, OSError):
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
                continue  # docstrings
            out.add(node.lineno)
    return out


# ---------------------------------------------------------------- running the check

def run(cmd, cwd, timeout, record=None, product=()):
    """Run the check once. With `record` (a folder), Python processes report what they ran."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    if record:
        write(os.path.join(record, "site", "sitecustomize.py"), SITECUSTOMIZE)
        env.update(CTC_ROOT=os.path.realpath(cwd), CTC_OUT=record, CTC_PRODUCT="|".join(product),
                   PYTHONPATH=os.path.join(record, "site") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""))
    start = time.time()
    try:
        p = subprocess.run(cmd, shell=True, cwd=cwd, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        out, code, timed_out = (p.stdout or "") + (p.stderr or ""), p.returncode, False
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) + \
              ((e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
        code, timed_out = None, True
    result = {"exit": code, "passed": code == 0, "timed_out": timed_out, "seconds": round(time.time() - start, 2),
              "tail": "\n".join(out.strip().splitlines()[-12:])}
    if not result["passed"] and (timed_out or code in (126, 127) or BLOCKED.search(out)):
        result["blocked"] = True
    if record:
        result["record"] = read_record(record)
    return result


def read_record(folder):
    rec = {"loaded": set(), "started": set(), "raised": set(), "lines": {}, "line_measured": False, "measured": False}
    for name in os.listdir(folder):
        if not name.startswith("rec."):
            continue
        rec["measured"] = True
        for ln in read(os.path.join(folder, name)).splitlines():
            parts = ln.split("\t")
            if parts[0] == "S" and len(parts) >= 4:
                rec["started"].add((parts[1], int(parts[2])))
            elif parts[0] == "U" and len(parts) >= 3:
                rec["raised"].add((parts[1], int(parts[2])))
            elif parts[0] == "L" and len(parts) >= 3:
                rec["lines"].setdefault(parts[1], set()).add(int(parts[2]))
            elif parts[0] == "F" and len(parts) >= 2:
                rec["loaded"].add(parts[1])
            elif parts[0] == "M":
                rec["line_measured"] = True
    return rec


def tests_seen(root, rec):
    """Test functions in the test files this run loaded: [(file, line, name, started, raised)]."""
    files = {f for f in rec["loaded"] if is_test(f) and f.endswith(".py")}
    out = []
    for f in sorted(files):
        for (first, defline), name in sorted(test_functions(os.path.join(root, f)).items()):
            started = (f, first) in rec["started"] or (f, defline) in rec["started"]
            raised = (f, first) in rec["raised"] or (f, defline) in rec["raised"]
            out.append({"file": f, "line": defline, "name": name, "started": started, "raised": raised})
    return out


def infer_product(root, rec):
    """Non-test repo .py files with functions that the check imported (their module code ran)."""
    return sorted(f for f in rec["loaded"] | set(rec["lines"])
                  if f.endswith(".py") and not is_test(f) and not SUPPORT.search(f.rsplit("/", 1)[-1])
                  and os.path.isfile(os.path.join(root, f))
                  and defines_function(os.path.join(root, f)))


def never_loaded(root, rec):
    """Python test files with test functions that this check never imported: [(file, count)]."""
    out = []
    for base, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_SCAN]
        for n in sorted(names):
            r = rel(os.path.join(base, n), root)
            if n.endswith(".py") and is_test(r) and r not in rec["loaded"]:
                count = len(test_functions(os.path.join(root, r)))
                if count:
                    out.append((r, count))
    return sorted(out)


# ---------------------------------------------------------------- mutants

def mutants(source, limit):
    lines = source.splitlines()
    try:
        original = ast.dump(ast.parse(source))
    except (SyntaxError, ValueError):
        original = None
    out, seen = [], set()
    for no, line in enumerate(lines, 1):
        if not line.strip() or COMMENT.match(line) or STRING_ONLY.match(line) or line.lstrip().startswith(("def ", "class ", "import ", "from ", '"""', "'''")):
            continue
        variants = []  # every match of every operator: a table row holds several constants
        quoted = [m.span() for m in QUOTED.finditer(line)]
        for name, pattern, repl in OPERATORS:
            hits = [m for m in re.finditer(pattern, line)
                    if not any(a <= m.start() < b for a, b in quoted)]  # a message is not behavior
            for match in hits[:PER_LINE]:
                new = match.expand(repl) if isinstance(repl, str) else repl(match)
                variants.append((name, line[:match.start()] + new + line[match.end():]))
        for name, after in variants:
            if after == line or (no, after) in seen:
                continue
            if original is not None:
                trial = list(lines)
                trial[no - 1] = after
                try:
                    if ast.dump(ast.parse("\n".join(trial))) == original:
                        continue
                except (SyntaxError, ValueError):
                    continue
            seen.add((no, after))
            out.append({"line": no, "operator": name, "before": line.strip(), "after": after.strip(), "_after": after})
            if len(out) >= limit:
                return out
    return out


def try_mutants(repo, cmd, product, limit, timeout, jobs, reached):
    work = []
    for f in product:
        src = read(os.path.join(repo, f))
        for m in mutants(src, limit):
            m["file"] = f
            work.append(m)
    work = work[:limit]
    if not work:
        return []
    lanes = [copy_repo(repo, tempfile.mkdtemp(prefix="ctc-lane-")) for _ in range(max(1, min(jobs, len(work))))]
    free = list(lanes)

    def one(m):
        lane = free.pop()
        try:
            path = os.path.join(lane, m["file"])
            original = read(path)
            lines = original.splitlines(True)
            ending = "\n" if lines[m["line"] - 1].endswith("\n") else ""
            lines[m["line"] - 1] = m["_after"].rstrip("\r\n") + ("\r\n" if lines[m["line"] - 1].endswith("\r\n") else ending)
            write(path, "".join(lines))
            r = run(cmd, lane, timeout)
            write(path, original)
            m["verdict"] = "survived" if r["passed"] else ("timeout" if r["timed_out"] else "caught")
            if m["verdict"] == "survived" and reached is not None:
                m["line_runs"] = m["line"] in reached.get(m["file"], set())
            return m
        finally:
            free.append(lane)

    try:
        with ThreadPoolExecutor(max_workers=len(lanes)) as pool:
            done = list(pool.map(one, work))
    finally:
        for lane in lanes:
            shutil.rmtree(lane, ignore_errors=True)
    for m in done:
        m.pop("_after", None)
    return done


# ---------------------------------------------------------------- base

def against_base(repo, cmd, base, timeout, now_tests):
    """Run the check with every non-test file changed since `base` put back as it was there.
    A test function that exists now but not at base, and passes there, can't catch the change."""
    changed = [f for f in git(repo, "diff", "--name-only", base, "--").splitlines() if f.strip()]
    untracked = [f for f in git(repo, "ls-files", "--others", "--exclude-standard").splitlines() if f.strip()]
    product = [f for f in changed + untracked if not is_test(f) and not f.lower().endswith((".md", ".txt", ".rst"))]
    scratch = copy_repo(repo, tempfile.mkdtemp(prefix="ctc-base-"))
    record = tempfile.mkdtemp(prefix="ctc-rec-")
    try:
        for f in product:
            try:
                write(os.path.join(scratch, f), git(repo, "show", f"{base}:{f}"))
            except RuntimeError:  # not in base: it was added since
                if os.path.exists(os.path.join(scratch, f)):
                    os.remove(os.path.join(scratch, f))
        r = run(cmd, scratch, timeout, record=record)
        rec = r.pop("record")
        old_names = set()
        for f in {t["file"] for t in now_tests}:
            try:
                tree_text = git(repo, "show", f"{base}:{f}")
            except RuntimeError:
                continue
            tmp = os.path.join(record, "old.py")
            write(tmp, tree_text)
            old_names |= {(f, n) for n in test_functions(tmp).values()}
        new = []
        for t in now_tests:
            if (t["file"], t["name"]) in old_names:
                continue
            seen = [s for s in tests_seen(scratch, rec) if s["file"] == t["file"] and s["name"] == t["name"]]
            state = "did not run" if not seen or not seen[0]["started"] else ("fails" if seen[0]["raised"] else "passes")
            new.append({**t, "on_base": state})
        return {"ref": base, "reverted": product, "passed": r["passed"], "exit": r["exit"],
                "measured": rec["measured"], "tail": r["tail"], "new_tests": new}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        shutil.rmtree(record, ignore_errors=True)


# ---------------------------------------------------------------- main

def check(repo, cmd, product=None, base=None, limit=60, timeout=None, jobs=4):
    repo = os.path.realpath(repo)
    scratch = copy_repo(repo, tempfile.mkdtemp(prefix="ctc-run-"))
    record = tempfile.mkdtemp(prefix="ctc-rec-")
    product = [p.replace("\\", "/").strip("/") for p in (product or [])]
    report = {"repo": repo, "check": cmd, "findings": []}
    try:
        first = run(cmd, scratch, timeout or 600, record=record, product=product)
        rec = first.pop("record")
        if not product and rec["measured"]:
            product = infer_product(scratch, rec)
            report["product_inferred"] = True
            if product:  # a second measured run, now recording product lines
                shutil.rmtree(record, ignore_errors=True)
                record = tempfile.mkdtemp(prefix="ctc-rec-")
                rec = run(cmd, scratch, timeout or 600, record=record, product=product).pop("record")
        report["product"] = product
        report["run"] = first
        tests = tests_seen(scratch, rec) if rec["measured"] else []
        report["measured"] = rec["measured"]
        report["tests"] = tests
        if first.get("blocked"):
            report["verdict"] = "blocked"
            return report
        if not first["passed"]:
            report["verdict"] = "red"
            report["failing"] = [t for t in tests if t["raised"]]
            return report
        for t in tests:
            if not t["started"]:
                report["findings"].append({"kind": "never-ran", **t})
        if rec["measured"] and any(is_test(f) for f in rec["loaded"]):
            for f, count in never_loaded(scratch, rec):
                report["findings"].append({"kind": "never-loaded", "file": f, "tests": count})
        if rec["measured"]:
            called = {f for f, _ in rec["started"]}
            for f in product:
                if f.endswith(".py") and f not in called:
                    report["findings"].append({"kind": "hollow", "file": f})
        reached = None
        if rec["line_measured"]:
            reached = rec["lines"]
            report["coverage"] = {f: {"reached": len(reached.get(f, set()) & code_lines(os.path.join(scratch, f))),
                                      "lines": len(code_lines(os.path.join(scratch, f)))}
                                  for f in product if f.endswith(".py")}
        per_run = max(10, int(first["seconds"] * 5) + 5)
        report["mutants"] = try_mutants(repo, cmd, product, limit, timeout or per_run, jobs, reached)
        for m in report["mutants"]:
            if m["verdict"] == "survived":
                report["findings"].append({"kind": "survived", **m})
        if base:
            report["base"] = against_base(repo, cmd, base, timeout or 600, tests)
            for t in report["base"]["new_tests"]:
                if t["on_base"] == "passes":
                    report["findings"].append({"kind": "passes-on-base", "file": t["file"], "line": t["line"],
                                               "name": t["name"], "ref": base})
            if report["base"]["passed"] and not report["base"]["new_tests"]:
                report["findings"].append({"kind": "base-green", "ref": base})
        report["verdict"] = "weak" if report["findings"] else "strong"
        if not product:
            report["verdict"] = "weak"
            report["findings"].append({"kind": "no-product"})
        return report
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        shutil.rmtree(record, ignore_errors=True)


def render(r):
    L = [f"check-the-check: {r['check']}   (ran in a scratch copy; the repo was not changed)"]
    run_ = r.get("run", {})
    ran = [t for t in r.get("tests", []) if t["started"]]
    state = "blocked" if run_.get("blocked") else ("pass" if run_.get("passed") else "FAIL")
    L.append(f"RUN        {state}  exit {run_.get('exit')}" + (f", {len(ran)} test functions ran" if r.get("measured") else ", not measured (not Python)"))
    if r["verdict"] in ("blocked", "red"):
        for t in r.get("failing", []):
            L.append(f"FAILING    {t['file']}:{t['line']} {t['name']}")
        L += ["           " + ln for ln in run_.get("tail", "").splitlines()]
        L.append(f"VERDICT    {r['verdict']}" + ("  the check could not run here; say where it does" if r["verdict"] == "blocked"
                                                 else "  the check fails now: that is the answer, not its strength"))
        return "\n".join(L)
    prod = ", ".join(r.get("product") or []) or "none found"
    L.append(f"PRODUCT    {prod}" + (" (inferred: what the check imports; pass --product to choose)" if r.get("product_inferred") else ""))
    for f, c in (r.get("coverage") or {}).items():
        L.append(f"LINES      {f}: {c['reached']}/{c['lines']} statements ran")
    for x in r["findings"]:
        if x["kind"] == "never-ran":
            L.append(f"NEVER RAN  {x['file']}:{x['line']} {x['name']}  (defined, never started: not collected or skipped)")
        elif x["kind"] == "never-loaded":
            L.append(f"NEVER LOADED {x['file']}  ({x['tests']} test functions): this check never imports it")
        elif x["kind"] == "hollow":
            L.append(f"HOLLOW     {x['file']}  imported, but no function in it was called")
        elif x["kind"] == "no-product":
            L.append("NO PRODUCT the check calls no repo code that could be mutated; pass --product")
    ms = r.get("mutants", [])
    if ms:
        n = {v: sum(m["verdict"] == v for m in ms) for v in ("caught", "survived", "timeout")}
        L.append(f"MUTANTS    {len(ms)} one-line bugs tried: {n['caught']} caught, {n['survived']} survived"
                 + (f", {n['timeout']} timed out" if n["timeout"] else ""))
        for m in ms:
            if m["verdict"] == "survived":
                where = "" if m.get("line_runs") is None else ("" if m["line_runs"] else "  (that line never runs)")
                L.append(f"SURVIVED   {m['file']}:{m['line']}  `{m['before']}`  ->  `{m['after']}`{where}")
    b = r.get("base")
    if b:
        L.append(f"BASE       {b['ref']}: put back {', '.join(b['reverted']) or 'no product file'}; check "
                 + ("passes" if b["passed"] else "fails") + " there")
        for t in b["new_tests"]:
            say = {"passes": "PASSES there: it cannot catch what this change fixed",
                   "fails": "fails there, passes now: it does catch the change",
                   "did not run": "did not run there"}[t["on_base"]]
            L.append(f"NEW TEST   {t['file']}:{t['line']} {t['name']}  {say}")
        if b["passed"] and not b["new_tests"]:
            L.append(f"           no test was added, and the check is green on {b['ref']} too: nothing here catches the change")
    survivors = sum(1 for x in r["findings"] if x["kind"] == "survived")
    L.append(f"VERDICT    {r['verdict']}" + (f"  ({survivors} survivor(s) to judge: a real gap, or no observable change)" if survivors else ""))
    return "\n".join(L)


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description="Would this check catch a bug? Runs it, plants one-line bugs, "
                                             "and compares against a base ref, all in scratch copies.")
    ap.add_argument("repo")
    ap.add_argument("--check", required=True, help="the command that runs the check, from the repo root")
    ap.add_argument("--product", nargs="*", help="files the check is meant to guard (default: the repo code it imports)")
    ap.add_argument("--base", help="git ref before the change: new tests must fail there")
    ap.add_argument("--max-mutants", type=int, default=60)
    ap.add_argument("--timeout", type=int, help="seconds per run (default: 5x the first run, at least 10)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.repo):
        print(f"no such folder: {a.repo}", file=sys.stderr)
        return 4
    for p in a.product or []:
        if not os.path.isfile(os.path.join(a.repo, p)):
            print(f"--product {p}: no such file in {a.repo}", file=sys.stderr)
            return 4
    try:
        r = check(a.repo, a.check, a.product, a.base, a.max_mutants, a.timeout, a.jobs)
    except RuntimeError as e:
        print(f"check-the-check: {e}", file=sys.stderr)
        return 4
    if a.json:
        print(json.dumps(r, indent=2, default=sorted))
    else:
        print(render(r))
    return {"strong": 0, "weak": 1, "red": 2, "blocked": 3}[r["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
