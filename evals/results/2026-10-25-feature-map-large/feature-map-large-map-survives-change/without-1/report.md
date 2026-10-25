I updated `fixture/CLAUDE.md` to match what the CLI actually does now. I ran every command against a throwaway copy of the code and notes, so your real `notes.json` was never written to. Its checksum is the same before and after, and all three notes are still there.

**What changed since the doc was written:**

1. **`search` is now called `find`.** Running `notes.py search ...` fails with exit 2. Searching works the same way under the new name (case-insensitive, includes archived notes).
2. **`due` reads dates as year-day-month (YYYY-DD-MM), even though its own help says YYYY-MM-DD.** If you type a date the normal way:
   - `due 1 2026-05-11` saves the date as **2026-11-05**, with no warning.
   - `due 1 2026-11-30` crashes.

   The cause is the date format string in `commands/due.py`.
3. **`upcoming` is broken.** It crashes with a TypeError as soon as any note has a due date, which your real notes do. The cause is that `commands/upcoming.py` compares a date with a datetime. `overdue` still works.

**Corrections to the doc that weren't from your teammate's change:**
- `debug-dump` isn't fully hidden from `--help`. It has no description, but it appears in the list of commands.
- `export` includes archived notes. I added that to the doc.

Everything else the doc says checked out: argument shapes, exit codes, the `pind`/`stard` typos, the crashes on an empty store, export/import duplicating notes, the hardcoded dates, `purge` refusing without `--yes`, and the purge log. `README.md` only points to `--help`, so it didn't need changes.

I only changed documentation, not code, so the `due` and `upcoming` bugs are still there. Until they're fixed, don't use `due` with a day of 12 or less, and run `overdue` instead of `upcoming`. Both are small fixes if you want me to make them.