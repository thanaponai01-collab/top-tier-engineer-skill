`FEATURES.md` now matches what the CLI does. I re-ran every recorded command against the new code, and `features.py check --rerun` comes back clean: 0 drifted, 0 regressed, 0 unmapped. Two commands are broken, and the doc now says so instead of calling them proven.

**What changed:**

1. **`search` was renamed to `find`.** `notes search` no longer exists and fails with "invalid choice". `notes find dune` works the same as before. I updated the Search entry, recorded a new run of `find`, and deleted the old receipt for the removed `search` command.

2. **`notes upcoming` crashes (exit 1)** on any note that has a due date: `TypeError: '<=' not supported between ... 'datetime.date' and 'datetime.datetime'`. In `commands/upcoming.py`, the end of the date range is now a datetime, but each note's due date is a plain date, and Python can't compare the two.

3. **`notes due` stores the wrong date without any error.** `commands/due.py` now reads the date as `%Y-%d-%m` (year-day-month), but its help text still says YYYY-MM-DD. So `due 3 2026-12-01` saves `2026-01-12`, and any date with a day above 12, like `2026-12-25`, crashes with a ValueError. The old check missed this because it only compares exit codes, which still said 0. I found it by comparing the actual output against the old receipts.

4. **Everything else works as recorded.** `overdue` and the other 25 commands gave the same output as before.

In `FEATURES.md`, the Due dates feature is now `status: failing`, with a `broken:` line for each of the two bugs. I also added the `--days` default (30) to its description. `README.md` and `AGENTS.md` don't mention any of these commands, so they needed no changes.

**Your notes:** `notes.json` is byte-for-byte unchanged; I checked its hash before and after every step. Every command that writes data ran in a throwaway copy. I also put a backup of `notes.json` and the old receipts in `backup/`, next to `fixture/`.

I only updated the docs and didn't touch your teammate's code. Both bugs are one-line fixes: change the format string in `due.py` to `'%Y-%m-%d'`, and compare dates with dates in `upcoming.py`. I can make those fixes and re-prove them if you want.