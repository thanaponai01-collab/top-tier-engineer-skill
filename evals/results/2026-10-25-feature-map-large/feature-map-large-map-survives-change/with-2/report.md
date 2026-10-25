`FEATURES.md` now matches what the CLI actually does, and a fresh `check --rerun` comes back clean: nothing stale, drifted, unmapped or regressed. Your `notes.json` is unchanged; its hash is the same before and after. Every command that writes ran in a throwaway copy, and I ran the full check in a separate copy of the repo too.

**What the teammate's changes did:**

1. **`search` was renamed to `find`.** `python notes.py search ...` now fails with "invalid choice". `find` works the same way (case-insensitive, titles and bodies). I updated the Search entry and its recorded run to `find`.

2. **`upcoming` is broken.** It crashes with a `TypeError` whenever any note has a due date. In `commands/upcoming.py` the end of the range is now a `datetime`, which can't be compared with the note's `date`. The Due dates feature is marked `failing` because of this.

3. **`due` saves the wrong date and doesn't say so.** The format string in `commands/due.py` was changed to `%Y-%d-%m`, so `due 1 2026-12-01` stores `2026-01-12`, and any day above 12 is rejected. The tool's own check missed this because it only compares exit codes, and this still exits 0. I found it by comparing outputs with the recorded runs. It's written down in the Due dates entry.

Everything else was re-run and still works with the same output: add, list, show, edit, rename, tags, archive, pin, star, stats, export/import, purge and `overdue`. The existing quirks are still there: pin and star print `pind` and `stard`, and stats/oldest/longest crash on an empty store.

I only changed the docs and the recorded runs under `.features/`, not the teammate's code. Fixing `due` and `upcoming` would be two one-line changes. Until then, don't run `due` on your real notes, because it will save the wrong date.