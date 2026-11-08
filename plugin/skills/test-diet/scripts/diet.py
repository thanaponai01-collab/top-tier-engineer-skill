"""diet.py - make tests shorter to read and faster to run, and refuse a diet that loses a bug the old tests caught.

    python diet.py <repo> [paths...]                 list leads -> .diet/candidates.md
    python diet.py <repo> --run "CMD" [--mutants N]  also record the suite, its times and the planted bugs it catches
    python diet.py <repo> --done                     check .diet/plan.json, write .diet/REPORT.md

Leads: setup repeated across tests (the path each replays to reach its state), slow tests and their
causes, tests that only check mocks. Python by AST; other test files by text. Leads, not verdicts.
"""
import argparse, ast, copy, hashlib, json, os, re, shutil, subprocess, sys, tempfile, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams  # noqa: E402

STATE = ".diet"
TIMER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_timer.py")
SKIP_DIRS = {".git", STATE, "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build",
             ".pytest_cache", ".mypy_cache", ".tox", ".idea", ".vscode", ".next", "coverage",
             ".states", ".cleanup", ".checkup"}
TEST_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".rb", ".go", ".java", ".kt", ".cs", ".php", ".rs"}
TESTS_RAN = re.compile(r"Ran (\d+) tests?|(\d+) passed|Tests?:\s+(\d+) passed|(\d+) tests? passed", re.I)
DURATION = re.compile(r"^\s*([\d.]+)s\s+(?:call|setup|teardown)\s+(\S+)", re.M)
SLOW_S = 0.25
WINDOW = 3          # statements (Python)
TEXT_WINDOW = 4     # lines (other languages)
SLOW_CALLS = {"sleep": "sleeps", "urlopen": "opens the network", "request": "opens the network",
              "get": None, "post": None, "Popen": "starts a process", "run": None, "check_output": "starts a process",
              "call": None, "system": "starts a process", "create_connection": "opens the network",
              "connect": None}
SLOW_MODULES = {"requests": "opens the network", "httpx": "opens the network", "urllib": "opens the network",
                "socket": "opens the network", "http": "opens the network", "subprocess": "starts a process",
                "time": None, "asyncio": None, "os": None}
MOCK_ATTRS = {"call_count", "called", "call_args", "call_args_list", "mock_calls", "await_count", "awaited"}


# ---------- files ----------

def walk(root, paths=None):
    tops = [os.path.join(root, p) for p in paths] if paths else [root]
    for top in tops:
        if os.path.isfile(top):
            yield os.path.relpath(top, root).replace("\\", "/")
            continue
        for here, dirs, names in os.walk(top):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.endswith(".egg-info"))
            for n in sorted(names):
                yield os.path.relpath(os.path.join(here, n), root).replace("\\", "/")


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def is_test(rel):
    parts = rel.split("/")
    name = parts[-1]
    return (any(p in ("tests", "test", "__tests__", "spec", "specs") for p in parts[:-1])
            or name == "conftest.py" or name.startswith("test_")
            or re.search(r"(_test\.\w+|\.test\.\w+|\.spec\.\w+|Test\.\w+|_spec\.rb)$", name) is not None)


def test_files(root, paths=None):
    return [r for r in walk(root, paths) if is_test(r) and os.path.splitext(r)[1].lower() in TEST_EXT]


def digest(root, rel):
    with open(os.path.join(root, *rel.split("/")), "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def app_hashes(root):
    return {r: digest(root, r) for r in walk(root) if not is_test(r)}


def test_lines(root):
    n = 0
    for r in test_files(root):
        text = read(root, r)
        if text:
            n += sum(1 for line in text.splitlines() if line.strip())
    return n


def h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


# ---------- Python tests by AST ----------

def call_name(func):
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def is_assertion(stmt):
    if isinstance(stmt, ast.Assert):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        n = call_name(stmt.value.func) or ""
        return n.lower().startswith(("assert", "fail", "expect")) or n in ("raises",)
    if isinstance(stmt, (ast.With, ast.AsyncWith)):
        return any(isinstance(i.context_expr, ast.Call) and
                   (call_name(i.context_expr.func) or "").lower().startswith(("assert", "raises")) for i in stmt.items)
    return False


def is_mock_assertion(stmt):
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        n = call_name(stmt.value.func) or ""
        if n.startswith("assert_") and isinstance(stmt.value.func, ast.Attribute):
            return True
    return any(isinstance(n, ast.Attribute) and n.attr in MOCK_ATTRS for n in ast.walk(stmt))


class Norm(ast.NodeTransformer):
    def __init__(self, local):
        self.local = local

    def visit_Name(self, node):
        if node.id in self.local:
            return ast.copy_location(ast.Name(id="L$" + node.id, ctx=node.ctx), node)
        return node

    def visit_arg(self, node):
        return node

    def visit_Constant(self, node):
        return ast.copy_location(ast.Constant(value="C"), node)


def units(rel, text):
    """Every function in a test file: (qualname, node, is_test)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    out = []

    def visit(body, cls):
        for node in body:
            if isinstance(node, ast.ClassDef):
                visit(node.body, node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out.append(((cls + "::" if cls else "") + node.name, node, node.name.startswith("test")))
    visit(tree.body, None)
    return out


def canonical(rel, qual):
    return f"{rel}::{qual}"


def py_scan(rel, text):
    """(windows, tests): windows = [(hash, unit id, index, statements)]; tests = per-test facts."""
    windows, tests = [], {}
    for qual, fn, test in units(rel, text):
        uid = canonical(rel, qual)
        local = {a.arg for a in fn.args.args + fn.args.kwonlyargs if a.arg not in ("self", "cls")}
        local |= {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        dumps = []
        for s in body:
            dumps.append(None if is_assertion(s) else ast.dump(Norm(local).visit(copy.deepcopy(s))))
        for i in range(len(body) - WINDOW + 1):
            chunk = dumps[i:i + WINDOW]
            if None in chunk:
                continue
            names = {}
            joined = re.sub(r"L\$(\w+)", lambda m: names.setdefault(m.group(1), f"v{len(names)}"), "\n".join(chunk))
            windows.append((h(joined), uid, i, body[i:i + WINDOW]))
        if test:
            asserts = [s for s in fn.body if is_assertion(s)]
            causes = slow_causes(fn)
            tests[uid] = {"path": rel, "line": fn.lineno, "mock_only": bool(asserts) and all(is_mock_assertion(s) for s in asserts),
                          "causes": causes}
    return windows, tests


def slow_causes(fn):
    found = set()
    for n in ast.walk(fn):
        if not isinstance(n, ast.Call):
            continue
        name = call_name(n.func)
        base = n.func.value.id if isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) else None
        if name == "sleep" and base in (None, "time", "asyncio"):
            found.add(f"sleeps (line {n.lineno})")
        elif base in SLOW_MODULES and SLOW_MODULES[base]:
            found.add(f"{SLOW_MODULES[base]} (line {n.lineno})")
        elif name in SLOW_CALLS and SLOW_CALLS[name] and base not in ("self", "mock") and name != "sleep":
            found.add(f"{SLOW_CALLS[name]} (line {n.lineno})")
    return sorted(found)


def calls_in(stmts):
    seen = []
    for s in stmts:
        cs = sorted((n for n in ast.walk(s) if isinstance(n, ast.Call)), key=lambda n: (n.lineno, n.col_offset))
        for c in cs:
            name = call_name(c.func)
            if name and (not seen or seen[-1] != name):
                seen.append(name)
    return seen


# ---------- other test files by text ----------

STRING = re.compile(r"([\"'`])(?:\\.|(?!\1).)*\1")
NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")
NOISE = re.compile(r"^[\s{}()\[\];,]*$")
TEXT_ASSERT = re.compile(r"\b(expect|assert\w*|should|t\.Error|t\.Fatal|require\.)\b")


def text_scan(rel, text):
    kept = []
    for no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or NOISE.match(s) or s.startswith(("//", "#", "/*", "*")):
            continue
        kept.append((no, None if TEXT_ASSERT.search(s) else NUMBER.sub("N", STRING.sub("S", s))))
    windows = []
    for i in range(len(kept) - TEXT_WINDOW + 1):
        chunk = kept[i:i + TEXT_WINDOW]
        if any(c[1] is None for c in chunk):
            continue
        windows.append((h("\n".join(c[1] for c in chunk)), f"{rel}:{chunk[0][0]}", i, (chunk[0][0], chunk[-1][0])))
    return windows


# ---------- find ----------

def group(windows, py):
    """Greedy: the biggest repeated windows first, extended while every copy still matches."""
    by = {}
    for w in windows:
        by.setdefault(w[0], []).append(w)
    seq = {}
    for w in windows:
        seq.setdefault(w[1] if py else w[1].rsplit(":", 1)[0], {})[w[2]] = w
    covered, groups = set(), []
    for key, ws in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if py:
            ws = list({w[1]: w for w in ws}.values())  # one copy per test function
        else:  # copies in one file must not overlap
            keep, last = [], {}
            for w in sorted(ws, key=lambda w: (w[1].rsplit(":", 1)[0], w[2])):
                f = w[1].rsplit(":", 1)[0]
                if f not in last or w[2] - last[f] >= TEXT_WINDOW:
                    keep.append(w)
                    last[f] = w[2]
            ws = keep
        if len(ws) < 2:
            continue
        unit = (lambda w: w[1]) if py else (lambda w: w[1].rsplit(":", 1)[0])
        if all((unit(w), w[2]) in covered for w in ws):
            continue
        length, hashes = 1, [key]
        while True:
            nxt = [seq[unit(w)].get(w[2] + length) for w in ws]
            if any(n is None for n in nxt) or len({n[0] for n in nxt}) != 1:
                break
            hashes.append(nxt[0][0])
            length += 1
        for w in ws:
            for k in range(length + (WINDOW if py else TEXT_WINDOW) - 1):
                covered.add((unit(w), w[2] + k))
        groups.append({"seed": key, "hashes": hashes, "copies": ws, "length": length})
    return groups


def find(root, paths=None):
    py_windows, text_windows, tests = [], [], {}
    for rel in test_files(root, paths):
        text = read(root, rel)
        if text is None:
            continue
        if rel.endswith(".py"):
            ws, ts = py_scan(rel, text)
            py_windows += ws
            tests.update(ts)
        else:
            text_windows += text_scan(rel, text)
    leads = []
    for g in group(py_windows, True):
        first = g["copies"][0]
        stmts = first[3]
        calls = calls_in(stmts)
        n = g["length"] + WINDOW - 1
        leads.append({"id": f"setup:{g['seed']}", "kind": "setup", "hashes": g["hashes"], "statements": n,
                      "calls": calls, "copies": [f"{w[1]} (from line {w[3][0].lineno})" for w in g["copies"]]})
    for g in group(text_windows, False):
        n = g["length"] + TEXT_WINDOW - 1
        leads.append({"id": f"setup:{g['seed']}", "kind": "setup", "hashes": g["hashes"], "statements": n,
                      "calls": [], "copies": [f"{w[1]}" for w in g["copies"]]})
    for uid, t in sorted(tests.items()):
        if t["mock_only"]:
            leads.append({"id": f"mock:{uid}", "kind": "mock", "test": uid, "at": f"{t['path']}:{t['line']}"})
    return leads, tests


def repeated_now(root, hashes):
    """How many places still hold any window of a block that was repeated."""
    seen = {}
    for rel in test_files(root):
        text = read(root, rel)
        if text is None:
            continue
        ws = py_scan(rel, text)[0] if rel.endswith(".py") else text_scan(rel, text)
        for w in ws:
            if w[0] in hashes:
                seen.setdefault(w[0], set()).add(w[1] if rel.endswith(".py") else w[1])
    return max((len(v) for v in seen.values()), default=0)


def slow_leads(tests, times):
    leads = []
    for uid in sorted(set(tests) | set(times)):
        t, s = tests.get(uid, {}), times.get(uid)
        causes = t.get("causes", [])
        if (s is not None and s >= SLOW_S) or causes:
            leads.append({"id": f"slow:{uid}", "kind": "slow", "test": uid, "seconds": s, "causes": causes,
                          "at": f"{t['path']}:{t['line']}" if t else uid})
    return sorted(leads, key=lambda l: -(l["seconds"] or 0))


def write_candidates(root, leads, record=None):
    md = ["# Test diet leads", "",
          "Leads, not verdicts. Each needs a change in `.diet/plan.json` that `covers` it, or a `kept` entry",
          "with a why. Only test files may change.", ""]
    if record:
        md += [f"Before: {record['lines']} test lines, {record['suite']['ran']} tests, "
               f"{record['suite']['seconds']:.2f} s, {len(record['caught'])} of {len(record['mutants'])} planted bugs caught.",
               ""]
    for l in leads:
        md.append(f"## {l['id']}")
        if l["kind"] == "setup":
            md.append(f"{l['statements']} {'statements' if l['calls'] else 'lines'} repeated in {len(l['copies'])} places"
                      + (f"; replays: {' -> '.join(l['calls'])}" if l["calls"] else ""))
            md += [f"- {c}" for c in l["copies"]]
        elif l["kind"] == "slow":
            md.append(f"{l['at']}: " + (f"{l['seconds']:.2f} s" if l["seconds"] is not None else "not timed")
                      + (f"; {', '.join(l['causes'])}" if l["causes"] else ""))
        else:
            md.append(f"{l['at']}: every assertion checks a mock, none checks a result")
        md.append("")
    if not leads:
        md.append("No leads: no repeated setup, no slow or mock-only tests found.")
    os.makedirs(os.path.join(root, STATE), exist_ok=True)
    with open(os.path.join(root, STATE, "candidates.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    return md


# ---------- run the tests ----------

def timed_cmd(cmd, out):
    if re.search(r"-m\s+unittest\b", cmd):
        return re.sub(r"-m\s+unittest\b", lambda _: f'"{TIMER}"', cmd, count=1), "unittest"
    if re.search(r"\bpytest\b", cmd):
        return cmd + " --durations=0 --durations-min=0", "pytest"
    return cmd, None


def run_tests(root, cmd, timeout=1800, timed=True, env=None):
    fd, out = tempfile.mkstemp(prefix="diet-times-", suffix=".json")
    os.close(fd)
    run_cmd, kind = timed_cmd(cmd, out) if timed else (cmd, None)
    e = dict(os.environ, DIET_TIMES=out, **(env or {}))
    t0 = time.perf_counter()
    try:
        p = subprocess.run(run_cmd, shell=True, cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=e)
        code, text = p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired:
        code, text = 124, "timed out"
    seconds = time.perf_counter() - t0
    times = {}
    if kind == "unittest":
        try:
            with open(out, encoding="utf-8") as fh:
                times = json.load(fh)
        except (OSError, ValueError):
            pass
    elif kind == "pytest":
        for m in DURATION.finditer(text):
            tid = re.sub(r"\[.*\]$", "", m.group(2))
            times[tid] = times.get(tid, 0.0) + float(m.group(1))
    try:
        os.remove(out)
    except OSError:
        pass
    counts = [int(g) for m in TESTS_RAN.finditer(text) for g in m.groups() if g]
    return {"cmd": cmd, "exit": code, "ran": max(counts) if counts else None, "seconds": seconds,
            "tail": text[-1500:], "times": times}


def map_times(times, tests):
    """unittest ids (pkg.mod.Class.test) and pytest ids (path::Class::test) onto path::Class::test."""
    dotted = {uid: uid.split("::", 1)[0][:-3].replace("/", ".") + "." + uid.split("::", 1)[1].replace("::", ".")
              for uid in tests}
    out = {}
    for tid, s in times.items():
        if tid in tests:
            out[tid] = s
            continue
        hit = next((uid for uid, d in dotted.items() if d == tid or d.endswith("." + tid)), None)
        out[hit or tid] = out.get(hit or tid, 0.0) + s
    return out


# ---------- planted bugs ----------

SWAP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt,
        ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot, ast.IsNot: ast.Is}


def points(tree):
    """Every place a small bug can be planted, in a fixed order."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and len(n.ops) == 1 and type(n.ops[0]) in SWAP:
            out.append((n, "compare"))
        elif isinstance(n, ast.BoolOp):
            out.append((n, "boolop"))
        elif isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
            out.append((n, "arith"))
        elif isinstance(n, ast.Constant) and type(n.value) is int:
            out.append((n, "int"))
        elif isinstance(n, ast.Constant) and type(n.value) is bool:
            out.append((n, "bool"))
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            out.append((n, "not"))
    return out


def plant(text, index):
    tree = ast.parse(text)
    pts = points(tree)
    node, kind = pts[index]
    line = getattr(node, "lineno", 0)
    if kind == "compare":
        node.ops[0] = SWAP[type(node.ops[0])]()
    elif kind == "boolop":
        node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
    elif kind == "arith":
        node.op = ast.Sub() if isinstance(node.op, ast.Add) else ast.Add()
    elif kind == "int":
        node.value += 1
    elif kind == "bool":
        node.value = not node.value
    elif kind == "not":
        class Drop(ast.NodeTransformer):
            def visit_UnaryOp(self, n):
                self.generic_visit(n)
                return n.operand if n is node else n
        tree = Drop().visit(tree)
    return ast.unparse(tree), line, kind


def imported_app_files(root):
    """App .py files the Python tests import, directly."""
    app = {r for r in walk(root) if r.endswith(".py") and not is_test(r)}
    found = set()
    for rel in test_files(root):
        if not rel.endswith(".py"):
            continue
        try:
            tree = ast.parse(read(root, rel) or "")
        except SyntaxError:
            continue
        mods = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods += [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                mods.append(n.module)
                mods += [n.module + "." + a.name for a in n.names]
        for m in mods:
            base = m.replace(".", "/")
            for pre in ("", "src/"):
                for cand in (f"{pre}{base}.py", f"{pre}{base}/__init__.py"):
                    if cand in app:
                        found.add(cand)
    return sorted(found)


def mutants(root, n):
    pool = []
    for rel in imported_app_files(root):
        try:
            count = len(points(ast.parse(read(root, rel) or "")))
        except SyntaxError:
            continue
        pool += [(rel, i) for i in range(count)]
    if not pool or n <= 0:
        return []
    step = max(1, len(pool) / n)
    picked = sorted({pool[int(k * step)] for k in range(min(n, len(pool)))})
    out = []
    for rel, i in picked:
        _, line, kind = plant(read(root, rel), i)
        out.append({"id": f"{rel}#{i}", "path": rel, "index": i, "line": line, "kind": kind})
    return out


def caught(root, cmd, muts, timeout):
    """Which planted bugs make the tests fail, run in a copy of the tree."""
    tmp = tempfile.mkdtemp(prefix="diet-mut-")
    try:
        for rel in walk(root):
            dst = os.path.join(tmp, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, *rel.split("/")), dst)
        hit = []
        for m in muts:
            path = os.path.join(tmp, *m["path"].split("/"))
            with open(path, encoding="utf-8") as fh:
                original = fh.read()
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(plant(original, m["index"])[0])
            r = run_tests(tmp, cmd, timeout=timeout, timed=False, env={"PYTHONDONTWRITEBYTECODE": "1"})
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(original)
            if r["exit"] != 0:
                hit.append(m["id"])
        return hit
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------- record / done ----------

def load(root, name):
    try:
        with open(os.path.join(root, STATE, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(root, name, data):
    os.makedirs(os.path.join(root, STATE), exist_ok=True)
    with open(os.path.join(root, STATE, name), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)


def done(root):
    record = load(root, "record.json")
    if not record:
        print("refused: no record. Run `--run \"<test cmd>\"` before you change anything.")
        return 1
    plan = load(root, "plan.json")
    if plan is None:
        print("refused: .diet/plan.json is missing or not valid JSON.")
        return 1
    problems = []
    changes = plan.get("changes", [])
    covered = {}
    for c in changes:
        if not str(c.get("what", "")).strip():
            problems.append(f"a change covering {c.get('covers')} says nothing in `what`")
        for cid in c.get("covers", []):
            covered[cid] = c
    kept = {}
    for k in plan.get("kept", []):
        if str(k.get("why", "")).strip():
            kept[k.get("candidate")] = k["why"]
        else:
            problems.append(f"kept {k.get('candidate')} with no reason")
    # app untouched
    now_app = app_hashes(root)
    before_app = record["app"]
    for rel in sorted(set(before_app) | set(now_app)):
        if rel not in now_app:
            problems.append(f"app file {rel} went away: this skill changes test files only")
        elif rel not in before_app:
            problems.append(f"app file {rel} is new: put helpers in a test folder or conftest.py")
        elif now_app[rel] != before_app[rel]:
            problems.append(f"app file {rel} changed: this skill changes test files only")
    suite = run_tests(root, record["suite"]["cmd"])
    _, tests_now = find(root)
    times_now = map_times(suite["times"], tests_now)
    for lead in record["leads"]:
        lid = lead["id"]
        if lid not in covered:
            if lid not in kept:
                problems.append(f"{lid} is neither covered by a change nor kept with a reason")
            continue
        if lead["kind"] == "setup":
            left = repeated_now(root, set(lead["hashes"]))
            if left >= 2:
                problems.append(f"{lid} is covered but part of it is still repeated in {left} places")
        elif lead["kind"] == "slow":
            t = lead["test"]
            if t in times_now and lead["seconds"] is not None:
                s = times_now[t]
                if s >= 0.1 and s > lead["seconds"] / 2:
                    problems.append(f"{lid} is covered but takes {s:.2f} s, was {lead['seconds']:.2f} s "
                                    f"(needs half or under 0.1 s)")
            elif t in tests_now and tests_now[t]["causes"] and lead["causes"]:
                problems.append(f"{lid} is covered but still {', '.join(tests_now[t]['causes'])}")
        elif lead["kind"] == "mock":
            t = lead["test"]
            if t in tests_now and tests_now[t]["mock_only"]:
                problems.append(f"{lid} is covered but still checks only mocks")
    if suite["exit"] != 0:
        problems.append(f"the tests passed before and fail now ({record['suite']['cmd']}):\n{suite['tail'][-800:]}")
    lines = test_lines(root)
    if lines > record["lines"]:
        problems.append(f"the tests got longer: {lines} lines now, {record['lines']} before")
    base_s = record["suite"]["seconds"]
    if suite["seconds"] > base_s * 1.25 + 0.5:
        problems.append(f"the tests got slower: {suite['seconds']:.2f} s now, {base_s:.2f} s before")
    lost = []
    if record["caught"] and not problems:
        muts = [m for m in record["mutants"] if m["id"] in set(record["caught"])]
        hit = set(caught(root, record["suite"]["cmd"], muts, record["timeout"]))
        lost = [m for m in muts if m["id"] not in hit]
        for m in lost:
            problems.append(f"a planted bug the old tests caught is missed now: {m['kind']} at {m['path']}:{m['line']} "
                            f"({m['id']}). Put back the check that caught it")
    if problems:
        print("DIET: refused")
        for p in problems:
            print(f"- {p}")
        return 1
    after = {"lines": lines, "ran": suite["ran"], "seconds": suite["seconds"], "caught": len(record["caught"])}
    write_report(root, record, after, changes, plan.get("kept", []))
    b = record["suite"]
    print(f"test lines {record['lines']} -> {lines}, tests {b['ran']} -> {suite['ran']}, "
          f"{b['seconds']:.2f} s -> {suite['seconds']:.2f} s, planted bugs caught "
          f"{len(record['caught'])}/{len(record['mutants'])} -> {len(record['caught'])}/{len(record['mutants'])}")
    print("report: .diet/REPORT.md")
    print("DIET: done")
    return 0


def write_report(root, record, after, changes, kept):
    b = record["suite"]
    pb = f"{len(record['caught'])} of {len(record['mutants'])}"
    md = ["# Test diet", "",
          "| | before | after |", "|---|---|---|",
          f"| test lines | {record['lines']} | {after['lines']} |",
          f"| tests | {b['ran']} | {after['ran']} |",
          f"| seconds | {b['seconds']:.2f} | {after['seconds']:.2f} |",
          f"| planted bugs caught | {pb} | {pb} |", "",
          "Planted bugs: small changes to the app code the tests import (a flipped comparison, an",
          "off-by-one). Every one the old tests caught, the new tests still catch.", ""]
    if not record["mutants"]:
        md += ["No planted bugs: no Python app file is imported by the tests, so deletions were not checked "
               "this way.", ""]
    md += ["## Changes", ""] + [f"- {c['what']} ({', '.join(c.get('covers', []))})"
                                + (f" at {c['at']}" if c.get("at") else "") for c in changes] + [""]
    if kept:
        md += ["## Kept", ""] + [f"- {k['candidate']}: {k['why']}" for k in kept] + [""]
    md += ["Not checked: tests that depend on run order, and flaky tests.", ""]
    with open(os.path.join(root, STATE, "REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--run", help="test command, e.g. \"python -m unittest discover tests\"")
    ap.add_argument("--mutants", type=int, default=20, help="planted bugs to try (default 20)")
    ap.add_argument("--done", action="store_true")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.repo)
    if a.done:
        return done(root)
    leads, tests = find(root, a.paths or None)
    if not a.run:
        leads += slow_leads(tests, {})
        print("\n".join(write_candidates(root, leads)[5:]))
        return 0
    suite = run_tests(root, a.run)
    if not suite["ran"]:
        print(f"refused: `{a.run}` ran no tests I could count, so nothing was recorded.\n{suite['tail'][-500:]}")
        return 1
    if suite["exit"] != 0:
        print(f"refused: the tests fail before any change, so a slimmer suite cannot be compared to them. "
              f"Fix or skip the red tests first.\n{suite['tail'][-800:]}")
        return 1
    times = map_times(suite["times"], tests)
    leads += slow_leads(tests, times)
    timeout = max(10.0, suite["seconds"] * 3)
    muts = mutants(root, a.mutants)
    hit = caught(root, a.run, muts, timeout) if muts else []
    record = {"suite": {k: suite[k] for k in ("cmd", "exit", "ran", "seconds")}, "times": times, "leads": leads,
              "lines": test_lines(root), "app": app_hashes(root), "mutants": muts, "caught": hit, "timeout": timeout}
    save(root, "record.json", record)
    print("\n".join(write_candidates(root, leads, record)[5:]))
    print(f"recorded: {suite['ran']} tests in {suite['seconds']:.2f} s"
          + ("" if times else " (not timed per test: use `python -m unittest ...` or `pytest`)")
          + f", {len(hit)} of {len(muts)} planted bugs caught. Slim the tests, write .diet/plan.json, then `--done`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
