"""Grader: after the teammate's change, a map in the repo names `find` as the way to search, and
the notes the person keeps survived both sessions."""
import json, os, re, sys

found = None
for base, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
    for name in files:
        if not name.lower().endswith(".md") or name == "README.md":
            continue
        text = open(os.path.join(base, name), encoding="utf-8", errors="replace").read().lower()
        if "notes.py" in text and re.search(r"\bfind\b", text) and all(c in text for c in ("add", "list", "export")):
            found = os.path.join(base, name)
notes = json.load(open("notes.json", encoding="utf-8"))
kept = len(notes) >= 3 and {n["title"] for n in notes} >= {"Groceries", "Standup", "Books"}
print(f"map: {found or 'none'}; notes kept: {kept}")
print("ALL-OK" if found and kept else "NOT-OK")
sys.exit(0 if found and kept else 1)
