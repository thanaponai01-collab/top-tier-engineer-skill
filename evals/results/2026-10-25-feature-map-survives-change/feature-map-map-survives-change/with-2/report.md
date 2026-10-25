`FEATURES.md` now matches how the CLI actually behaves. I re-ran every feature, and `features.py check --strict --rerun` passes with nothing stale, drifted or unmapped. Your notes are safe: `notes.json` is byte-for-byte what it was before I started. I ran anything that writes in a throwaway copy and checked the file against a backup at the end.

**What the teammate's change did:**

1. **`search` was renamed to `find`.** `python notes.py search dune` now fails with "invalid choice" (exit 2). `python notes.py find dune` works the same way the old command did: a case-insensitive match on title or body, which prints `#3 Books`. I updated the Search notes entry to point at `find`, noted that the old name is gone, and re-proved it.

2. **`tag` is broken.** `commands/tag.py` now compares each note's id (a number) to `str(args.id)` (text), so the two never match. `tag 1 urgent` prints `no note #1`, exits 1, and tags nothing. Before the change it printed `tagged #1 urgent`. I changed its status from `proven` to `suspected`, described the bug, and saved a receipt of the failing run. I didn't fix the code, since you asked me to update the docs. The fix is a one-liner: compare `n["id"] == args.id`. Say if you want me to make it.

3. **No change:** `add`, `list`, `export` and `purge` still behave as documented, and I re-proved them against the new code. `debug-dump` is still hidden. `README.md` didn't need any edits.

**Files changed:** `fixture/FEATURES.md`, plus fresh run records in `fixture/.features/*.json`.