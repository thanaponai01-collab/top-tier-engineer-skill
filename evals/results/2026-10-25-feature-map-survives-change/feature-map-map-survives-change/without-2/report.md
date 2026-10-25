I've updated `fixture/CLAUDE.md` to match how the CLI behaves now. `AGENTS.md` just points to it, and `README.md` only says to run `--help`, so neither needed changes. I tried every command on a temporary copy of the repo. Your real `notes.json` was never written to, and your 3 notes are still there.

**What your teammate's changes did:**

1. **`search` is now `find`.** It works the same way: a case-insensitive match on title or body. `python notes.py search …` now fails with an "invalid choice" error. The code is still in `commands/search.py`.
2. **`tag` is broken.** It now prints `no note #N`, exits with an error, and saves nothing, even for notes that exist (I tried `tag 1 x`). The cause is in `commands/tag.py`: it compares the note's id, which is a number, to the id as text (`str(args.id).strip()`), so no note ever matches. The old code compared them directly and worked. This looks like a bug, not a deliberate change. For now the only way to tag a note is `add --tag` when you create it.
3. **`export` got a longer help line** ("write all notes to a CSV file for spreadsheets"). It behaves the same as before.

`add`, `list`, `export`, `purge` (including refusing without `--yes`) and `debug-dump` all still work as the guide described.

**What I changed in CLAUDE.md:** renamed `search` to `find` in the list of commands that are safe to run and in the command table, and noted that the old name now fails. I marked `tag` as broken and explained why, added how to tag a note for now, and noted in the layout section that `find` is in `search.py`.

I only changed the docs, not the code. Fixing `tag` is a one-line change (`if n["id"] == args.id:`) if you want me to make it.