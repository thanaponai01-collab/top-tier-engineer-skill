`FEATURES.md` now matches what the CLI actually does. The repo's checker (`python .features/features.py check --strict --rerun`) passes with nothing stale, drifted or regressed. `notes.json` is byte-for-byte unchanged. Every command that writes data was run in a throwaway copy of the repo, never against your real notes.

**What your teammate's changes did:**

1. **`search` was renamed to `find`.** `python notes.py search dune` now fails with "invalid choice". It works as `python notes.py find dune` and still prints `#3 Books`. I changed the Search entry in `FEATURES.md` to use `find` and noted the rename. I also removed the old `search` record from `.features/search.json` and saved a new one for `find`.

2. **`tag` is now broken.** Every call fails with `no note #<id>` and exit code 1, even for notes that exist. The cause is in `commands/tag.py`: it compares the note's numeric id with `str(args.id).strip()`, which is text, so nothing ever matches. Because it fails before saving, it can't damage your notes. In `FEATURES.md` I changed Tag from "proven" to "traced: BROKEN" with this explanation. Its failing run is saved in `.features/tag.json`.

3. **Everything else still works** and I re-ran each one: `add` printed `added #4`, `list --tag home` showed notes #1 and #3, `export` wrote the CSV, and `purge --yes` deleted all notes (in the copy only).

I didn't fix the `tag` bug, since you asked me to document what works rather than change your teammate's code. The fix is one line in `commands/tag.py`: compare `n["id"] == args.id`. If you want it, I can make that change and re-prove Tag. `README.md` doesn't name any individual commands, so it needed no changes. I also deleted the `__pycache__` folders my test runs created.