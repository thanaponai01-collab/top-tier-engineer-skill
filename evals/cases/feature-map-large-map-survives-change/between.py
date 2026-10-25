"""A teammate's change between the two sessions, the same in both arms. Three of the 30 commands
move: `search` is renamed `find`; `due` now parses dates as %Y-%d-%m, so a real date like
2026-10-31 raises ValueError; `upcoming` now ends the window at the end of the day, a datetime,
and compares it with a date, so it raises TypeError whenever a note has a due date. The two
breaks read as plausible edits and show only when the command runs."""
import os, sys

root = sys.argv[1]


def edit(rel, old, new):
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))


edit("notes.py", '"search": search.run,', '"find": search.run,')
edit("notes.py", 'sub.add_parser("search"', 'sub.add_parser("find"')
edit("commands/due.py", "'%Y-%m-%d'", "'%Y-%d-%m'")
edit("commands/upcoming.py", "end = today + datetime.timedelta(days=args.days)",
     "end = datetime.datetime.combine(today + datetime.timedelta(days=args.days), datetime.time.max)")
