"""Grader: after the teammate's change, a map in the repo names `mood` as a command and covers the
field commands, and the notes the person keeps survived both sessions."""
import json, os, re, sys

texts = []  # a map may be an index with include: area files, so read every notes file together
for base, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
    for name in files:
        if name.lower().endswith(".md") and name != "README.md":
            texts.append(open(os.path.join(base, name), encoding="utf-8", errors="replace").read().lower())
text = "\n".join(texts)
found = bool("notes.py" in text and re.search(r"(?<![\w-])mood\b", text)
             and all(c in text for c in ("set-rating", "count-owner", "clear-sprint")))
notes = json.load(open("notes.json", encoding="utf-8"))
kept = len(notes) >= 3 and {n["title"] for n in notes} >= {"Groceries", "Standup", "Books"}
print(f"map: {found}; notes kept: {kept}")
print("ALL-OK" if found and kept else "NOT-OK")
sys.exit(0 if found and kept else 1)
