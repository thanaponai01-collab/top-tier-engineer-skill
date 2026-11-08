"""states.py - find the state machines a codebase never declared, and refuse a map that misses part of one.

    python states.py <repo> [paths...]       list candidate state fields -> .states/candidates.md
    python states.py <repo> --run "CMD"      also record the tests and a copy of the tree before any change
    python states.py <repo> --done           check .states/machines.json, write .states/MACHINES.md

Python is read by AST; JS and TS by text patterns. Candidates are leads, not verdicts.
"""
import argparse, ast, json, os, re, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams  # noqa: E402

STATE = ".states"
SKIP_DIRS = {".git", STATE, "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build",
             ".pytest_cache", ".mypy_cache", ".tox", ".idea", ".vscode", ".next", "coverage"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
TESTS_RAN = re.compile(r"Ran (\d+) tests?|(\d+) passed|Tests?:\s+(\d+) passed|(\d+) tests? passed", re.I)
WRONG_REASON = re.compile(r"ModuleNotFoundError|ImportError|No module named|SyntaxError|NameError|"
                          r"Cannot find module|is not defined|error: unrecognized arguments|not found: ", re.I)
JS_WRITE = re.compile(r"(?<![=!<>])\b(\w+)\.(\w+)\s*=\s*(?:([\"'`])([\w\- ]+)\3|(true|false|null)\b)(?!\s*=)")
JS_CHECK = re.compile(r"\.(\w+)\s*[!=]==?\s*([\"'])([\w\- ]+)\2|([\"'])([\w\- ]+)\4\s*[!=]==?\s*\w+\.(\w+)\b")
JS_FUNC = re.compile(r"(?:function\s+(\w+)|(\w+)\s*\([^)]*\)\s*\{|(\w+)\s*[:=]\s*(?:async\s*)?\([^)]*\)\s*=>)")
BOOLISH = (ast.Compare, ast.BoolOp)


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
    return (any(p in ("tests", "test", "__tests__", "spec") for p in parts[:-1])
            or name.startswith("test_") or name.endswith(("_test.py", ".test.js", ".test.ts", ".spec.js",
                                                         ".spec.ts", ".test.tsx", ".spec.tsx")))


# ---------- find ----------

def literal(node):
    """('str', v) / ('bool', v) / ('none', None) / None for anything computed."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return ("bool", node.value)
        if isinstance(node.value, str):
            return ("str", node.value)
        if node.value is None:
            return ("none", None)
    return None


def boolish(node):
    return (isinstance(node, BOOLISH) or (isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not))
            or (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool"))


def field_of(node):
    if isinstance(node, ast.Attribute) and not node.attr.startswith("__"):
        return node.attr
    if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
        return node.slice.value
    return None


def strings_in(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
    return []


def scan_python(rel, text, writes, checks):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return

    def visit(node, func, cls):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func = f"{cls}.{node.name}" if cls and func == "<module>" else node.name
        elif isinstance(node, ast.ClassDef):
            cls = node.name
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                name = field_of(t)
                if not name:
                    continue
                lit = literal(node.value)
                kind = lit[0] if lit else ("bool" if boolish(node.value) else "expr")
                value = lit[1] if lit else None
                owner = cls if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self" else None
                writes.append({"field": name, "kind": kind, "value": value, "path": rel, "line": node.lineno,
                               "func": func, "owner": owner})
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = node.left, node.comparators[0]
            for a, b in ((left, right), (right, left)):
                name = field_of(a)
                if name:
                    for v in strings_in(b):
                        checks.append({"field": name, "value": v, "path": rel, "line": node.lineno, "func": func})
        for child in ast.iter_child_nodes(node):
            visit(child, func, cls)

    visit(tree, "<module>", None)


def scan_js(rel, text, writes, checks):
    func = "<module>"
    for no, line in enumerate(text.splitlines(), 1):
        m = JS_FUNC.search(line)
        if m and not line.strip().startswith(("if", "for", "while", "switch", "return")):
            func = next(g for g in m.groups() if g)
        for m in JS_WRITE.finditer(line):
            obj, name, _, s, kw = m.groups()
            if s is not None:
                kind, value = "str", s
            else:
                kind, value = ("none", None) if kw == "null" else ("bool", kw == "true")
            writes.append({"field": name, "kind": kind, "value": value, "path": rel, "line": no, "func": func,
                           "owner": rel if obj == "this" else None})
        for m in JS_CHECK.finditer(line):
            name = m.group(1) or m.group(6)
            value = m.group(3) if m.group(1) else m.group(5)
            checks.append({"field": name, "value": value, "path": rel, "line": no, "func": func})


def find(root, paths=None):
    writes, checks = [], []
    for rel in walk(root, paths):
        if is_test(rel):
            continue
        ext = os.path.splitext(rel)[1].lower()
        if ext == ".py" or ext in JS_EXT:
            text = read(root, rel)
            if text is not None:
                (scan_python if ext == ".py" else scan_js)(rel, text, writes, checks)
    cands = []
    by_field = {}
    for w in writes:
        by_field.setdefault(w["field"], []).append(w)
    # string fields: written as string literals in two or more places
    for name, ws in sorted(by_field.items()):
        strs = [w for w in ws if w["kind"] == "str"]
        if len(strs) < 2:
            continue
        written = sorted({w["value"] for w in strs})
        cs = [c for c in checks if c["field"] == name]
        checked = sorted({c["value"] for c in cs})
        cands.append({"id": f"field:{name}", "kind": "string", "fields": [name], "writes": ws, "checks": cs,
                      "written": written, "checked": checked,
                      "never_set": [v for v in checked if v not in written],
                      "never_checked": [v for v in written if v not in checked]})
    # flag groups: fields of one class written as booleans (or None) in two or more places
    groups = {}
    for name, ws in by_field.items():
        own = [w for w in ws if w["owner"]]
        if not own or any(w["kind"] == "str" for w in ws):
            continue
        if len([w for w in ws if w["kind"] in ("bool", "none")]) < 2:
            continue
        for owner in {w["owner"] for w in own}:
            groups.setdefault((own[0]["path"], owner), set()).add(name)
    for (path, owner), names in sorted(groups.items()):
        names = sorted(names)
        if len(names) < 2 or not any(w["kind"] == "bool" for n in names for w in by_field[n]):
            continue
        ws = [w for n in names for w in by_field[n]]
        cands.append({"id": f"flags:{path}:{owner}", "kind": "flags", "fields": names, "writes": ws, "checks": [],
                      "combinations": 2 ** len(names)})
    for c in cands:
        c["writes"] = sorted(c["writes"], key=lambda w: (w["path"], w["line"]))
    return cands


def where(x):
    return f"{x['path']}:{x['line']} ({x['func']})"


def shown(w):
    if w["kind"] == "expr" or (w["kind"] == "bool" and w["value"] is None):
        return "<computed>"
    return repr(w["value"]) if w["kind"] == "str" else str(w["value"])


def write_candidates(root, cands):
    md = ["# State-machine candidates", "",
          "Leads, not verdicts. Map each one in `.states/machines.json` or dismiss it with a reason.",
          "Every write below must be a transition (`at`) or listed in `also` with why. `at` is",
          "`path:line` or `path:function`.", ""]
    suspects = []
    for c in cands:
        md.append(f"## {c['id']}")
        if c["kind"] == "string":
            md.append(f"values written: {', '.join(c['written'])}")
            if c["never_set"]:
                md.append(f"**checked but never set: {', '.join(c['never_set'])}**")
                suspects += [f"value:{c['fields'][0]}={v}" for v in c["never_set"]]
            if c["never_checked"]:
                md.append(f"written but never compared: {', '.join(c['never_checked'])}")
        else:
            md.append(f"flags: {', '.join(c['fields'])} ({c['combinations']} combinations; which are legal?)")
        md.append("writes:")
        md += [f"- {where(w)} {w['field']} = {shown(w)}" for w in c["writes"]]
        if c["checks"]:
            md.append("checks:")
            md += [f"- {where(k)} == {k['value']!r}" for k in c["checks"]]
        md.append("")
    if not cands:
        md.append("No candidates: no field is set to a string or a flag in two or more places.")
    os.makedirs(os.path.join(root, STATE), exist_ok=True)
    with open(os.path.join(root, STATE, "candidates.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    return md, suspects


# ---------- record ----------

def run_tests(root, cmd):
    try:
        p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "exit": 124, "ran": None, "tail": "timed out"}
    out = p.stdout + p.stderr
    counts = [int(g) for m in TESTS_RAN.finditer(out) for g in m.groups() if g]
    return {"cmd": cmd, "exit": p.returncode, "ran": max(counts) if counts else None, "tail": out[-1500:]}


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


def copy_tree(src, dst, rels):
    for rel in rels:
        target = os.path.join(dst, *rel.split("/"))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(os.path.join(src, *rel.split("/")), target)


# ---------- done ----------

def matches(at, w):
    at = str(at).replace("\\", "/")
    path, _, spot = at.rpartition(":")
    if path != w["path"]:
        return False
    return spot == str(w["line"]) or spot == w["func"] or spot == w["func"].split(".")[-1]


def prove(root, record, f):
    """A bug's test must fail on the tree as it was (with today's tests laid over it)."""
    before = os.path.join(root, STATE, "before")
    old = set(record["files"])
    over = [r for r in walk(root) if r not in old or is_test(r)]
    proofs = os.path.join(root, STATE, "proofs")
    kept = [f"{STATE}/proofs/{r}" for r in walk(proofs)] if os.path.isdir(proofs) else []
    tmp = tempfile.mkdtemp(prefix="states-before-")
    try:
        copy_tree(before, tmp, record["files"])
        copy_tree(root, tmp, over + kept)
        then = run_tests(tmp, f["test"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    now = run_tests(root, f["test"])
    return then, now


def done(root):
    record = load(root, "record.json")
    if not record:
        print("refused: no record. Run `--run \"<test cmd>\"` before you change anything.")
        return 1
    m = load(root, "machines.json")
    if m is None:
        print("refused: .states/machines.json is missing or not valid JSON.")
        return 1
    cands = record["candidates"]
    problems = []
    machines = m.get("machines", [])
    findings = m.get("findings", [])
    covered = {c for f in findings for c in f.get("covers", [])}
    dismissed = {}
    for d in m.get("dismissed", []):
        if str(d.get("why", "")).strip():
            dismissed[d.get("candidate")] = d["why"]
        else:
            problems.append(f"dismissed {d.get('candidate')} with no reason")
    mapped = {}
    for mc in machines:
        for fld in mc.get("fields", []):
            for key in {fld, "field:" + fld}:
                mapped.setdefault(key, []).append(mc)
        for a in mc.get("also", []):
            if not str(a.get("why", "")).strip():
                problems.append(f"{mc.get('name')}: `also` {a.get('at')} has no why")
    for c in cands:
        mcs = mapped.get(c["id"])
        if not mcs:
            if c["id"] not in dismissed:
                problems.append(f"{c['id']} is in no machine and not dismissed with a reason")
            continue
        # one field name can belong to several machines (Article.status, Delivery.status): read them together
        names = " / ".join(mc.get("name", "?") for mc in mcs)
        states = {s for mc in mcs for s in mc.get("states", [])}
        ats = [t.get("at") for mc in mcs for t in mc.get("transitions", [])]
        ats += [a.get("at") for mc in mcs for a in mc.get("also", []) if str(a.get("why", "")).strip()]
        for w in c["writes"]:
            # a constructor setting a literal is the starting value, not a move; computed ones still need a why
            starts = w["func"].split(".")[-1] in ("__init__", "constructor") and w["kind"] != "expr"
            if not starts and not any(a and matches(a, w) for a in ats):
                problems.append(f"{names}: the write at {where(w)} ({w['field']}) is in no transition and not in `also`")
        if c["kind"] == "string":
            for v in c["written"]:
                if v not in states:
                    problems.append(f"{names}: {c['fields'][0]} is set to {v!r} but that is not one of its states")
            for v in c["never_set"]:
                if f"value:{c['fields'][0]}={v}" not in covered:
                    problems.append(f"{c['fields'][0]} is checked for {v!r}, which nothing sets: no finding covers "
                                    f"value:{c['fields'][0]}={v}")
    for mc in machines:
        name = mc.get("name", "?")
        states = set(mc.get("states", []))
        terminal = set(mc.get("terminal", []))
        trans = mc.get("transitions", [])
        if not states:
            problems.append(f"{name}: no states")
        for t in trans:
            if not t.get("at"):
                problems.append(f"{name}: transition {t.get('from')} -> {t.get('to')} has no `at`")
            if t.get("to") not in states:
                problems.append(f"{name}: transition to {t.get('to')!r}, which is not a state")
            if t.get("from") not in states and t.get("from") != "*":
                problems.append(f"{name}: transition from {t.get('from')!r}, which is not a state")
        for s in sorted(states - terminal):
            if not any(t.get("from") in (s, "*") for t in trans) and f"deadend:{name}:{s}" not in covered:
                problems.append(f"{name}: nothing leaves {s!r}. Mark it terminal, or cover deadend:{name}:{s} with a finding")
    proofs = []
    for f in findings:
        if not str(f.get("what", "")).strip():
            problems.append(f"a finding covering {f.get('covers')} says nothing in `what`")
        if f.get("kind") == "bug":
            if not f.get("test"):
                problems.append(f"bug {f.get('what', '?')[:60]!r} has no test command that reaches it")
                continue
            then, now = prove(root, record, f)
            proofs.append((f, then, now))
            if then["exit"] == 0:
                problems.append(f"bug {f['what'][:60]!r}: `{f['test']}` passes on the tree as it was, so it does not "
                                f"reach the bug")
            elif WRONG_REASON.search(then["tail"]):
                problems.append(f"bug {f['what'][:60]!r}: `{f['test']}` fails on the tree as it was for a reason that "
                                f"is not the bug:\n{then['tail'][-400:]}")
            if f.get("fixed") and now["exit"] != 0:
                problems.append(f"bug {f['what'][:60]!r} is marked fixed but `{f['test']}` fails now:\n{now['tail'][-400:]}")
            if not f.get("fixed") and now["exit"] == 0:
                problems.append(f"bug {f['what'][:60]!r} is marked open but `{f['test']}` passes now: mark it fixed")
        elif not str(f.get("why", "")).strip() and f.get("covers"):
            problems.append(f"finding {f.get('what', '?')[:60]!r} is not a bug and gives no why")
    base = record["suite"]
    now = run_tests(root, base["cmd"])
    if base["exit"] == 0 and now["exit"] != 0:
        problems.append(f"the tests passed before and fail now ({base['cmd']}):\n{now['tail'][-800:]}")
    if base["ran"] and (now["ran"] or 0) < base["ran"]:
        problems.append(f"fewer tests ran: {now['ran']} now, {base['ran']} before")
    if problems:
        print("STATES: refused")
        for p in problems:
            print(f"- {p}")
        return 1
    write_machines(root, machines, findings, m.get("dismissed", []), proofs)
    print(f"tests: {now['ran']} ran, {'passing' if now['exit'] == 0 else 'failing as before'}")
    print(f"{len(machines)} machines, {sum(1 for f in findings if f.get('kind') == 'bug')} bugs proven "
          f"({sum(1 for f in findings if f.get('kind') == 'bug' and f.get('fixed'))} fixed). Map: .states/MACHINES.md")
    print("STATES: done")
    return 0


def node(s):
    return re.sub(r"\W", "_", str(s)) or "_"


def write_machines(root, machines, findings, dismissed, proofs):
    md = ["# State machines", ""]
    for mc in machines:
        name = mc.get("name", "?")
        md += [f"## {name}", "", f"fields: {', '.join(mc.get('fields', []))}", "", "```mermaid", "stateDiagram-v2"]
        if mc.get("initial"):
            md.append(f"    [*] --> {node(mc['initial'])}")
        states = mc.get("states", [])
        for t in mc.get("transitions", []):
            froms = [s for s in states if s != t["to"]] if t.get("from") == "*" else [t["from"]]
            for fr in froms:
                md.append(f"    {node(fr)} --> {node(t['to'])}: {t.get('label') or str(t['at']).rsplit(':', 1)[-1]}")
        for s in mc.get("terminal", []):
            md.append(f"    {node(s)} --> [*]")
        md += ["```", ""]
        mine = [f for f in findings if f.get("machine") == name]
        for f in mine:
            tag = "bug, fixed" if f.get("kind") == "bug" and f.get("fixed") else ("bug, open" if f.get("kind") == "bug" else "ok")
            md.append(f"- **{tag}**: {f.get('what')}" + (f" ({f['at']})" if f.get("at") else "")
                      + (f" Test: `{f['test']}`" if f.get("test") else "") + (f" Why: {f['why']}" if f.get("why") else ""))
        md.append("")
    rest = [f for f in findings if f.get("machine") not in {mc.get("name") for mc in machines}]
    if rest:
        md += ["## Other findings", ""] + [f"- {f.get('what')}" for f in rest] + [""]
    if dismissed:
        md += ["## Not state machines", ""] + [f"- {d['candidate']}: {d['why']}" for d in dismissed] + [""]
    with open(os.path.join(root, STATE, "MACHINES.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))


def main(argv=None):
    utf8_streams()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--run", help="test command, e.g. \"python -m unittest discover tests\"")
    ap.add_argument("--done", action="store_true")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.repo)
    if a.done:
        return done(root)
    cands = find(root, a.paths or None)
    md, suspects = write_candidates(root, cands)
    print("\n".join(md[6:]))
    if suspects:
        print("each of these needs a finding: " + ", ".join(suspects))
    if a.run:
        suite = run_tests(root, a.run)
        if not suite["ran"]:
            print(f"refused: `{a.run}` ran no tests I could count, so nothing was recorded.\n{suite['tail'][-500:]}")
            return 1
        files = list(walk(root))
        before = os.path.join(root, STATE, "before")
        shutil.rmtree(before, ignore_errors=True)
        copy_tree(root, before, files)
        save(root, "record.json", {"files": files, "suite": suite, "candidates": cands})
        print(f"recorded: {suite['ran']} tests, exit {suite['exit']}, and the tree as it was in .states/before/. "
              f"Map, prove, fix, then `--done`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
