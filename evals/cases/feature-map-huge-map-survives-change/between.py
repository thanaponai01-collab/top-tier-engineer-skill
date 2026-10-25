"""A teammate's change between the two sessions, the same in both arms, touching 4 of 133 commands:
`show-mood` is renamed `mood`; `set-rating` gains range validation with the condition inverted, so
every valid rating is refused; `count-owner` drops the str() from its sort key, so it raises
TypeError when a note has no owner; `clear-sprint` keeps history by popping the field, then prints
it, so it raises KeyError. Each reads as a plausible edit and shows only when the command runs."""
import os, sys

root = sys.argv[1]


def edit(rel, old, new):
    path = os.path.join(root, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new, 1))


edit("notes.py", 'sub.add_parser("show-mood"', 'sub.add_parser("mood"')
edit("commands/fields/rating.py", "    return int(value)",
     '    if 1 <= int(value) <= 5:\n        raise SystemExit("rating must be 1-5")\n    return int(value)')
edit("commands/fields/owner.py", "key=lambda kv: str(kv[0])", "key=lambda kv: kv[0]")
edit("commands/fields/sprint.py",
     "    n[FIELD] = None\n    store.save(notes)\n    print(f\"#{n['id']} {FIELD} cleared\")",
     "    n.setdefault(\"history\", []).append(n.pop(FIELD))\n    store.save(notes)\n"
     "    print(f\"#{n['id']} {FIELD} cleared (was {n[FIELD]})\")")
