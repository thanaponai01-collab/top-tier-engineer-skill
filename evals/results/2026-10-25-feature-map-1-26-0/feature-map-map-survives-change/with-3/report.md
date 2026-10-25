I've updated `fixture/FEATURES.md` to match how the CLI behaves now. The repo's own strict check, which re-runs every recorded proof, now passes with nothing stale, drifted or regressed.

**What changed in the teammate's push:**

1. **`search` is now called `find`.** `python notes.py find dune` still prints `#3 Books`. The old `python notes.py search ...` now fails with exit 2 ("invalid choice"), so anyone used to `search` will hit that error. I updated the entry and re-ran the proof under the new name. I also removed the old `search` proof record, since that command no longer exists.
2. **`tag` is broken.** `commands/tag.py` now compares each note's id, which is a number, against `str(args.id)`, which is text. They never match, so every call prints `no note #<id>`, exits 1, and adds nothing. I tried ids 1, 2 and 3 in throwaway copies and all failed. FEATURES.md now says it's broken, and I changed its status from "proven" to "suspected". I didn't fix the code: that's the teammate's change, and you asked for the docs to be brought up to date. The fix is one line, comparing `n["id"] == args.id`. Want me to make it?
3. **Everything else still works:** `add`, `list`, `export` and `purge` (still refuses without `--yes`). I re-ran each one; their notes in FEATURES.md were still accurate. `debug-dump` is still the hidden developer command.

`README.md` needed no changes. It only points to `--help` and `export`, and both still work.

**Your notes are safe.** Everything that writes data ran in throwaway copies. `notes.json` has the same checksum (sha256 `b6c46891…`) as before I started, and no `out.csv` or `purge.log` was left in `fixture/`.