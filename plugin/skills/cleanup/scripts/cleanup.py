"""cleanup.py - find what agents leave behind, and refuse "done" while the cleanup broke something.

    python cleanup.py <repo> [paths...]          list candidates -> .cleanup/candidates.md
    python cleanup.py <repo> --run "CMD"         also record files and tests before any change
    python cleanup.py <repo> --done --run "CMD"  check the cleanup, save .cleanup/history.json

Python is read by AST. Other files by name and text only. Candidates are leads, not verdicts.
"""
import argparse, ast, datetime, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _encoding import utf8_streams  # noqa: E402

STATE = ".cleanup"
SKIP_DIRS = {".git", STATE, "__pycache__", "node_modules", ".venv", "venv", "env", "dist", "build",
             ".pytest_cache", ".mypy_cache", ".tox", ".idea", ".vscode"}
TEXT_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".json", ".toml", ".yaml", ".yml",
            ".ini", ".cfg", ".md", ".txt", ".rst", ".sh", ".ps1", ".bat", ".html", ".css", ".go",
            ".rs", ".java", ".rb", ".php", ".sql", ".env", ""}
LEFTOVER = re.compile(r"(?:[_\-.](?:v\d+|old|new|bak|backup|copy|final|fixed|tmp|temp|orig|draft|unused)"
                      r"|\s\(\d+\)|\scopy)$", re.I)
LITTER_NAME = re.compile(r"(summary|changes[_-]?made|implementation[_-]?notes|progress|fix[_-]?notes|"
                         r"debug|scratch|output)", re.I)
LITTER_EXT = {".log", ".bak", ".orig", ".tmp", ".swp", ".rej"}
SCRATCH = re.compile(r"^(test_fix|test_quick|quick_test|debug_|scratch|try_|tmp_|check_)", re.I)
DEBUG_LINE = re.compile(r"print\(\s*f?[\"']DEBUG|console\.log\(|\bbreakpoint\(\)|pdb\.set_trace\(|debugger;")
STUB_LINE = re.compile(r"(TODO|FIXME|XXX)\b.*\b(implement|stub|placeholder|fake|later)|\bplaceholder\b", re.I)
CHANGE_NOTE = re.compile(r"^\s*(#|//)\s*(updated|fixed|changed|new|added|refactored|modified|rewritten)\b"
                         r"[^\n]*(bug|version|v\d|rewrite|previous|now|earlier|fix)", re.I)
TESTS_RAN = re.compile(r"Ran (\d+) tests?|(\d+) passed|Tests?:\s+(\d+) passed|(\d+) tests? passed", re.I)


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
    path = os.path.join(root, rel)
    if os.path.splitext(rel)[1].lower() not in TEXT_EXT or os.path.getsize(path) > 1_000_000:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def corpus(root):
    return {rel: text for rel in walk(root) if (text := read(root, rel)) is not None}


def is_test(rel):
    parts = rel.split("/")
    return any(p in ("tests", "test", "__tests__", "spec") for p in parts[:-1])


def mentioned(word, texts, besides):
    pat = re.compile(r"(?<![\w])" + re.escape(word) + r"(?![\w])")
    return [rel for rel, t in texts.items() if rel not in besides and pat.search(t)]


def normalized(fn):
    """The function body with every local name, argument and docstring erased."""
    names = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    body = fn.body[1:] if (fn.body and isinstance(fn.body[0], ast.Expr)
                          and isinstance(getattr(fn.body[0], "value", None), ast.Constant)) else fn.body

    class Erase(ast.NodeTransformer):
        def visit_Name(self, n):
            return ast.Name(id="_" if n.id in names else n.id, ctx=n.ctx)

        def visit_arg(self, n):
            return ast.arg(arg="_")
    return ast.dump(ast.Module(body=[Erase().visit(ast.parse(ast.unparse(b))) for b in body], type_ignores=[]))


def scan_python(rel, text, texts, found, bodies):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    used |= {n.value.id for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    exported = re.search(r"__all__", text)
    if not rel.endswith("__init__.py") and not exported:
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in node.names:
                    name = (a.asname or a.name).split(".")[0]
                    if a.name != "*" and name not in used and not re.search(r"\b%s\b" % re.escape(name),
                                                                             text.replace(ast.get_source_segment(text, node) or "", "")):
                        found.append(("unused-import", rel, node.lineno, name))
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Continue)):
            found.append(("swallowed-error", rel, node.lineno, "except: " + type(node.body[0]).__name__.lower()))
        if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and any(isinstance(c, ast.Constant) for c in node.test.comparators)
                and len(node.body) == 1 and isinstance(node.body[0], ast.Return)
                and isinstance(node.body[0].value, ast.Constant) and not is_test(rel)):
            found.append(("hard-coded-answer", rel, node.lineno, ast.unparse(node.test)[:60]))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [b for b in node.body if not (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant))]
            if len(body) == 1 and (isinstance(body[0], ast.Pass) or (
                    isinstance(body[0], ast.Raise) and "NotImplementedError" in ast.unparse(body[0]))):
                found.append(("stub", rel, node.lineno, node.name))
            if len(body) >= 2:
                bodies.setdefault(normalized(node), []).append((rel, node.lineno, node.name))
    if is_test(rel):
        return
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("__"):
            here = len(re.findall(r"(?<![\w])%s(?![\w])" % re.escape(node.name), text))
            if here <= 1 and not mentioned(node.name, texts, {rel}) and not node.decorator_list:
                found.append(("dead-function", rel, node.lineno, node.name))


def scan_comments(rel, text, found):
    lines = text.splitlines()
    run = []
    for i, line in enumerate(lines + [""], 1):
        s = line.strip()
        if s.startswith("#") and not s.startswith("#!") and len(s) > 1:
            run.append((i, s.lstrip("#")[1:] if s.lstrip("#").startswith(" ") else s.lstrip("#")))
            continue
        if len(run) >= 2:
            code = "\n".join(t for _, t in run)
            try:
                ast.parse(code)
                if re.search(r"[=(:]", code):
                    found.append(("commented-out-code", rel, run[0][0], f"{len(run)} lines"))
            except SyntaxError:
                pass
        run = []


def find(root, paths=None):
    texts = corpus(root)
    found, bodies = [], {}
    names = list(walk(root, paths))
    for rel in names:
        base = os.path.basename(rel)
        stem, ext = os.path.splitext(base)
        top = "/" not in rel
        if LEFTOVER.search(stem):
            found.append(("leftover-version", rel, 0, base))
        elif ext.lower() in LITTER_EXT or (top and ext.lower() in (".md", ".txt") and LITTER_NAME.search(stem)
                                           and stem.upper() not in ("README", "CHANGELOG", "CONTRIBUTING", "LICENSE")):
            found.append(("litter", rel, 0, base))
        elif top and ext == ".py" and SCRATCH.search(stem):
            found.append(("litter", rel, 0, base + " (scratch script outside the tests)"))
        if ext == ".py" and stem != "__init__" and not is_test(rel) and not mentioned(stem, texts, {rel}):
            if not re.search(r"__name__\s*==\s*[\"']__main__", texts.get(rel, "")):
                found.append(("orphan-module", rel, 0, stem + " is named by no other file"))
        text = texts.get(rel)
        if text is None:
            continue
        if ext == ".py":
            scan_python(rel, text, texts, found, bodies)
            scan_comments(rel, text, found)
        for i, line in enumerate(text.splitlines(), 1):
            if ext in (".md", ".txt", ".rst", ".json"):
                break
            if DEBUG_LINE.search(line):
                found.append(("debug-leftover", rel, i, line.strip()[:60]))
            if STUB_LINE.search(line):
                found.append(("stub", rel, i, line.strip()[:60]))
            if CHANGE_NOTE.search(line):
                found.append(("change-log-comment", rel, i, line.strip()[:60]))
    for copies in bodies.values():
        if len(copies) > 1:
            where = ", ".join(f"{r}:{n} {f}" for r, n, f in copies)
            for r, n, f in copies:
                found.append(("duplicate-function", r, n, f"{f} (same body: {where})"))
    seen, out = set(), []
    for item in found:
        key = item[:3]
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def key(c):
    return f"{c[0]}|{c[1]}|{c[3].split(' ')[0]}"


def run_tests(root, cmd):
    p = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
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


def since_last(root, cands):
    hist = load(root, "history.json") or []
    if not hist:
        return []
    last = hist[-1]
    before = set(last.get("left", []))
    lines = [f"Since the cleanup of {last['date']}:"]
    new = [c for c in cands if key(c) not in before]
    back = [f for f in last.get("deleted", []) if os.path.exists(os.path.join(root, f))]
    lines += [f"  came back: {f} (deleted then)" for f in back]
    lines += [f"  new: {c[0]} {c[1]}{':%d' % c[2] if c[2] else ''} {c[3]}" for c in new]
    if len(lines) == 1:
        lines.append("  nothing new and nothing came back")
    return lines


def write_candidates(root, cands, extra):
    groups = {}
    for c in cands:
        groups.setdefault(c[0], []).append(c)
    md = ["# Cleanup candidates", "", "Leads, not verdicts: read each before you act. Swallowed errors, stubs and",
          "hard-coded answers change behavior when fixed; say so if you fix one.", ""]
    md += extra + ([""] if extra else [])
    for kind in sorted(groups):
        md.append(f"## {kind} ({len(groups[kind])})")
        md += [f"- {c[1]}{':%d' % c[2] if c[2] else ''}  {c[3]}" for c in groups[kind]]
        md.append("")
    os.makedirs(os.path.join(root, STATE), exist_ok=True)
    with open(os.path.join(root, STATE, "candidates.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))
    return md


def git_head(root):
    p = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def done(root, cmd):
    base = load(root, "baseline.json")
    if not base:
        print("CLEANUP: not done - no baseline. Run `--run CMD` before changing anything.")
        return 1
    if cmd is None:
        cmd = base["suite"]["cmd"]
    problems = []
    now = run_tests(root, cmd)
    was = base["suite"]
    if was["exit"] == 0 and now["exit"] != 0:
        problems.append(f"the tests passed before and fail now ({cmd}):\n{now['tail'][-800:]}")
    if was["ran"] and (now["ran"] or 0) < was["ran"]:
        problems.append(f"{now['ran'] or 0} tests ran, {was['ran']} before")
    deleted = [f for f in base["files"] if not os.path.exists(os.path.join(root, f))]
    texts = corpus(root)
    for f in deleted:
        stem = os.path.splitext(os.path.basename(f))[0]
        if stem in ("__init__", "index", "main"):
            continue
        refs = mentioned(stem, texts, set()) if len(stem) > 2 else []
        if refs:
            problems.append(f"deleted {f}, but '{stem}' is still named in {', '.join(refs[:5])}"
                            " - make sure nothing loads it by that name, then update or remove the mention")
    cands = find(root)
    if problems:
        print("CLEANUP: not done")
        for p in problems:
            print("  - " + p)
        return 1
    hist = load(root, "history.json") or []
    hist.append({"date": datetime.date.today().isoformat(), "commit": git_head(root),
                 "deleted": deleted, "left": [key(c) for c in cands],
                 "tests": {"before": was["ran"], "after": now["ran"]}})
    save(root, "history.json", hist)
    os.remove(os.path.join(root, STATE, "baseline.json"))
    print(f"deleted {len(deleted)} files; tests {was['ran']} before, {now['ran']} after, "
          f"{'passing' if now['exit'] == 0 else 'failing as before'}; {len(cands)} candidates left (.cleanup/candidates.md)")
    write_candidates(root, cands, [])
    print("CLEANUP: done")
    return 0


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
        return done(root, a.run)
    cands = find(root, a.paths or None)
    extra = since_last(root, find(root))
    md = write_candidates(root, cands, extra)
    print("\n".join(md[5:]))
    if a.run:
        suite = run_tests(root, a.run)
        if not suite["ran"]:
            print(f"refused: `{a.run}` ran no tests I could count, so nothing was recorded.\n{suite['tail'][-500:]}")
            return 1
        save(root, "baseline.json", {"files": list(walk(root)), "suite": suite})
        print(f"recorded: {suite['ran']} tests, exit {suite['exit']}. Clean up, then `--done`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
