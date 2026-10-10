"""Grader: a diagram of the service was saved in the repo (not only shown in chat), and it draws
the reports route reaching the database directly."""
import os, re, sys

hits = []
for base, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
    for name in files:
        if name == "README.md" or not name.lower().endswith((".md", ".html", ".mmd", ".svg", ".txt")):
            continue
        text = open(os.path.join(base, name), encoding="utf-8", errors="replace").read()
        drawn = re.search(r"```mermaid|<pre class=.mermaid|flowchart|graph (LR|TD|TB)|-->|──>|->", text)
        if drawn and "report" in text.lower() and "db" in text.lower():
            hits.append(os.path.join(base, name))
print("diagram saved:", hits or "none")
sys.exit(0 if hits else 1)
