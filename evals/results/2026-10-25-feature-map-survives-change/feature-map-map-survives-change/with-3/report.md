`FEATURES.md` now matches what the CLI actually does, and `features.py check --strict --rerun` passes with nothing stale, drifted or regressed. I re-ran every command: anything that writes ran only in a throwaway copy. `notes.json` is byte-identical to before.

**What changed:**

1. **`search` is now `find`.** `python notes.py search dune` now fails with "invalid choice". `find dune` works the same as before: it matches title or body, ignoring case, and printed `#3 Books`. The map now lists `find` and marks it proven again. I deleted the old `search` record from `.features/search.json` because that command no longer exists.

2. **`tag` is broken — a new bug.** `tag 1 urgent` now prints `no note #1` and exits 1, for every id. In `commands/tag.py`, the line `if n["id"] == str(args.id).strip():` compares the number id stored in `notes.json` with a string, so it never matches. I changed Tag from **proven** to **traced: BROKEN** and wrote down the cause. I didn't fix the code, because you asked for the docs to reflect what works. The fix is one line, `if n["id"] == args.id:`, and I can apply it if you want.

3. **Unchanged and confirmed working:** `add`, `list --tag`, `export` and `purge --yes` all behave as documented. They only needed fresh proof records because `notes.py` had changed.

The check passing doesn't mean everything works. It means the docs are now accurate, and they say `tag` is broken. `README.md` didn't need any changes.