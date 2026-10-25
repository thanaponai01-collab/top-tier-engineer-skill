"""A teammate's change between the two sessions, the same in both arms and mentioned to neither:
ops want to know how many retried rows the export sent, so `dedupe` is rewritten to count them.
The rewrite checks each row against every row kept so far, which is quadratic again: about 3 s on
last night's export and minutes on the tenfold one. The first row still wins, so every figure the
report prints is unchanged and the suite stays green unless a guard times it."""
import ast
import os
import sys

root = sys.argv[1]
path = os.path.join(root, "report.py")
with open(path, encoding="utf-8") as fh:
    text = fh.read()
func = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "dedupe")
lines = text.splitlines(keepends=True)
start = (func.decorator_list[0].lineno if func.decorator_list else func.lineno) - 1
new = '''def dedupe(rows):
    """The export retries, so an order can appear more than once. The first row wins.

    Ops track how often the export retries, so the dropped rows are counted on stderr.
    """
    kept = []
    retried = 0
    for row in rows:
        if any(k["order_id"] == row["order_id"] for k in kept):
            retried += 1
            continue
        kept.append(row)
    print(f"dedupe: {retried} retried rows dropped", file=sys.stderr)
    return kept
'''
text = "".join(lines[:start]) + new + "".join(lines[func.end_lineno:])
if "import sys" not in text.split("def ", 1)[0]:
    text = "import sys\n" + text
with open(path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
