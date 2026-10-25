I've updated `fixture/FEATURES.md` and the run records to match what the CLI actually does now. The final `features.py check --rerun` comes back clean: nothing stale, drifted, unmapped or regressed. Two date commands are now marked **failing** because they really are broken.

**What your teammate changed**

1. **`search` was renamed to `find`.** `python notes.py search …` now fails with "invalid choice". `find dune` works and matches note #3 Books, the same as before. The code behind it is still in `commands/search.py`. I updated the Search entry, re-recorded the run with `find`, and removed the old `search` record.

2. **`due` is broken: it now reads dates as year-day-month.** `commands/due.py` parses with `%Y-%d-%m`, but the help text still says YYYY-MM-DD.
   - A day above 12 crashes it: `due 1 2026-12-25` fails with a `ValueError`.
   - A day of 12 or less is silently swapped: `due 1 2026-12-01` saves **2026-01-12**. That note then shows up as overdue.
   - The automatic recheck didn't catch the swap, because it only checks whether the command exits cleanly. I confirmed it by hand in a throwaway copy.

3. **`upcoming` is broken.** `upcoming --days 60` crashes with a `TypeError` (`commands/upcoming.py:6` compares a date with a datetime).

`overdue` still works; nothing is overdue as of the default date, 2026-10-25. The other 10 features behave exactly as recorded, so I re-recorded them against the new code and left their write-ups as they were. `README.md` and `AGENTS.md` don't mention any of the changed commands, so I didn't edit them.

**Your notes:** `fixture/notes.json` is byte-for-byte unchanged, checked by hash before and after. Every command that writes data ran in a throwaway copy. I also kept a backup at `backup/notes.json.orig` next to `fixture/`.

I only updated the docs and left the two bugs in the code alone. Both are one-line fixes: changing the date format in `due.py` back to `%Y-%m-%d`, and comparing against a plain date in `upcoming.py`. Do you want me to fix them, or leave them for your teammate?