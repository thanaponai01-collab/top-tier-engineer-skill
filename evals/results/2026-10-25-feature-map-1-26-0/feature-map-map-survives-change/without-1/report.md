I've updated `fixture/AGENTS.md` to match how the CLI behaves now. `CLAUDE.md` just points to that file, and `README.md` doesn't name any commands, so neither needed changes. I ran every command against a temporary copy of the repo, and your real `notes.json` was never touched.

**What changed:**

1. **`search` was renamed to `find`** (in `notes.py`). The search itself works the same way: it ignores case and matches the title and body, not tags. Running `notes search …` now fails with an "invalid choice" error. The command table, the layout note (`find` is still handled by `commands/search.py`) and the "not supported" line now say `find`.

2. **`tag` is now broken.** `commands/tag.py` checks the note's id (a number) against `str(args.id).strip()` (text), so it never finds a match. Every call, including `tag 1 urgent` on a note that exists, prints `no note #1`, exits with code 1 and saves nothing. I marked it as broken in the docs and left the code alone, since it's your teammate's change. The fix is a one-line change to `if n["id"] == args.id:` if you want me to make it.

3. **Small fix to the docs:** they said `debug-dump` was hidden from `--help`. It has no description line, but it does appear in the list of command names, and the docs now say so.

**Unchanged and confirmed working:** `list` (including `--tag`), `add` (where new ids can repeat old ones after a purge), `export` (which overwrites the CSV without asking) and `purge`. Without `--yes`, `purge` refuses and exits with code 1. With it, it empties the notes and adds a line to `purge.log`. I also read through `debug-dump`'s code, which only prints `notes.json`.

`purge.py` also changed recently, but it still matches what the docs say.