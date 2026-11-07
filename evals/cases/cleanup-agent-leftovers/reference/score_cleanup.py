"""Count how much of the planted agent mess is gone. Run from the finished repo root.

Prints one line per item and `CLEANED n/12`. Exits 0 when at least PASS_AT are gone.
`--json` prints the items as JSON instead.
"""
import ast, json, os, re, sys

PASS_AT = 10


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def py_files():
    for here, dirs, names in os.walk("."):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "tests") and not d.startswith(".")]
        for n in names:
            if n.endswith(".py"):
                yield os.path.join(here, n)


def money_format_copies():
    """Functions anywhere whose body is the cents formatter, after renaming the argument."""
    copies = 0
    for path in py_files():
        try:
            tree = ast.parse(read(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and len(node.args.args) == 1:
                src = ast.unparse(node.body[-1]) if node.body else ""
                if "// 100" in src and "% 100:02d" in src:
                    copies += 1
    return copies


def imports(path):
    try:
        tree = ast.parse(read(path))
    except SyntaxError:
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.asname or a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            names |= {a.asname or a.name for a in node.names}
    return names


report = read("app/report.py")
export = read("app/export.py")
importer = read("app/importer.py")
items = {
    "orphan report_old.py deleted": not os.path.exists("app/report_old.py"),
    "IMPLEMENTATION_SUMMARY.md deleted": not os.path.exists("IMPLEMENTATION_SUMMARY.md"),
    "scratch test_fix.py deleted": not os.path.exists("test_fix.py"),
    "debug_output.txt deleted": not os.path.exists("debug_output.txt"),
    "dead legacy_totals removed": "def legacy_totals" not in report,
    "money formatter has one copy": money_format_copies() == 1,
    "report's own formatter copy gone": "def _fmt" not in report,
    "settings.py merged into config": not os.path.exists("app/settings.py") and "settings" not in importer,
    "DEBUG print removed": "DEBUG" not in read("app/store.py"),
    "commented-out export_csv_old removed": "export_csv_old" not in export,
    "unused imports removed": not ({"os", "json"} & imports("app/report.py")) and "re" not in imports("app/importer.py"),
    "stale change comment removed": not re.search(r"#\s*Updated:", report),
}
done = sum(items.values())
if "--json" in sys.argv:
    print(json.dumps({"cleaned": done, "items": items}))
else:
    for what, gone in items.items():
        print(f"{'done' if gone else 'left'}  {what}")
    print(f"CLEANED {done}/{len(items)}")
sys.exit(0 if done >= PASS_AT else 1)
