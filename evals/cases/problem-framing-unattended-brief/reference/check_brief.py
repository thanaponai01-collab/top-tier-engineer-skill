"""Grader: the framing was written down in the repo, not only said in chat, and it says what is
out of scope and what was assumed."""
import os, re, sys

for base, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
    for name in files:
        path = os.path.join(base, name)
        if not name.lower().endswith(".md") or path.replace("\\", "/").endswith("notes/client-call.md"):
            continue
        text = open(path, encoding="utf-8", errors="replace").read().lower()
        scoped = re.search(r"not building|out of scope|non-goals|won.t build|will not build|not in scope", text)
        assumed = re.search(r"assum", text)
        if scoped and assumed:
            print("framing saved:", path)
            sys.exit(0)
print("no saved framing with scope and assumptions")
sys.exit(1)
