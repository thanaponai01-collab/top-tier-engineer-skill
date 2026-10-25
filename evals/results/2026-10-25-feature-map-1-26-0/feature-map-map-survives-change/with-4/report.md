`FEATURES.md` now matches how the CLI actually behaves, and the repo's own check (`features.py check --rerun`) passes cleanly. One command, `tag`, is broken, and the doc now says so.

**What your teammate's push changed**

1. **`search` was renamed to `find`.** `python notes.py search dune` now fails with "invalid choice" (exit 2). `python notes.py find dune` works and prints `#3 Books`. I changed the Search entry to `find`, re-ran it, and deleted the old run record for `search` because that command no longer exists.
2. **`tag` is broken.** `python notes.py tag 1 urgent` prints `no note #1` and exits 1, even though note #1 exists. In `commands/tag.py`, the code compares the note's numeric id with `str(args.id).strip()`, which is text, so no note ever matches. Tag is now marked **failing** in `FEATURES.md`, with the cause. I didn't change the code because you asked for the docs to be brought up to date, not for fixes. The fix is one line, changing the comparison to `if n["id"] == args.id:`. Want me to make it?
3. **Add, List, Export and Purge** all work the same as before; I re-ran each one against the new code.

**Your notes:** `notes.json` is byte-for-byte unchanged, checked before and after. Add, tag, export and purge only ran in throwaway copies, never on the real file. I also saved a copy at `backup/notes.json`, next to `fixture/`.

`README.md` and `AGENTS.md` didn't need changes, since neither mentions `search` or `tag`.