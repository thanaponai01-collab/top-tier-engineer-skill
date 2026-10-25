"""A teammate's change between the two sessions, the same in both arms: "startup is slow, load the
event handlers only where stock changes". It moves `import app.handlers` out of shop.py's top level
into cmd_restock only, so `restock` still fires every handler and `sell` fires none: no audit line,
no reorder note, no low-stock alert on a sale. A test that imports app.handlers itself still passes."""
import os, re, sys

path = os.path.join(sys.argv[1], "shop.py")
with open(path, encoding="utf-8") as fh:
    text = fh.read()
line = re.search(r"(?m)^import app\.handlers.*\n", text)
assert line, "shop.py has no top-level `import app.handlers`"
text = text.replace(line.group(0), "", 1)
text, n = re.subn(r"(?m)^(def cmd_restock\(args\):\n)",
                  r"\1    import app.handlers  # noqa: F401  - loaded lazily: only stock changes need the handlers\n",
                  text, count=1)
assert n == 1, "shop.py has no cmd_restock"
with open(path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
