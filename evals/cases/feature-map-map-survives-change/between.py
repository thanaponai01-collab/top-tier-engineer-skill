"""A teammate's change between the two sessions, applied the same way in both arms: `search` is
renamed `find`, and `tag` now compares the note id to a string, so it never finds a note. Reading
tag.py it still looks right; running `tag 1 x` prints `no note #1` and exits 1."""
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
edit("notes.py", 'sub.add_parser("search", help="full-text search")', 'sub.add_parser("find", help="full-text search")')
edit("commands/tag.py", 'if n["id"] == args.id:', 'if n["id"] == str(args.id).strip():')
