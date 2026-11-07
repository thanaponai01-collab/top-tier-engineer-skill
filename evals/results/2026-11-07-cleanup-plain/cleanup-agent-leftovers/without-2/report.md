The cleanup is finished. All 7 tests pass. I saved what the read-only commands (`list`, `report`, and `export` in every format) printed before my changes, and afterwards the only difference is that the stray `DEBUG loaded…` line no longer appears. I also ran `import`, `add`, `migrate` and `scripts/backfill.py` on a throwaway copy of the repo, and they all still work. The real ledger was not touched.

## What I removed
- **`test_fix.py`** and **`debug_output.txt`**: a one-off check script and its saved output. The `tests/` folder already covers the same thing.
- **`IMPLEMENTATION_SUMMARY.md`**: an agent's own report. It says "fixed the rounding bug" and "all tests pass", but that was only true because of a fake shortcut (next point). It would have misled the next agent.
- **A faked result in `app/report.py`**: `monthly_total` had `if month == "2026-01": return 123456`, which returns the exact number the test expects. Underneath it, the code added up absolute values, so refunds were counted as spending. I replaced both with a plain sum. January really does come to 123456 that way, and any month with a refund now comes out right instead of too high. **This is the one change that alters behaviour**, and it's a fix.
- **Also in `report.py`**: unused imports (`json`, `os`), two functions nothing called (`legacy_totals`, `summary_line`), and a private copy of the money formatter.
- **`app/report_old.py`**: an old version of the report module that nothing imported.
- **`app/settings.py`**: a near-copy of `app/config.py`. Its only user, `importer.py`, now uses `config.load_config()` instead. I also removed an unused `import re` there.
- **In `app/export.py`**: a copy of the money formatter (it now uses `app.money.format_money`) and a commented-out old CSV exporter.
- **In `app/store.py`**: a leftover `print("DEBUG loaded …")`. It went into normal output, so every `export` (including JSON) started with a junk line.

## What I kept that looks like mess
- **`app/migrate_v2.py`**: nothing imports it directly, but `config.json` names it (`"migration": "migrate_v2"`) and `budget.py migrate` loads it by that name.
- **`app/formats/qif.py` and `ofx.py`**: these also look unused, but `budget.py export qif|ofx` loads them by name.
- **`scripts/backfill.py`**: the README tells you to run it when upgrading old ledgers.

## Things I didn't change that you should know about
1. **OFX export doesn't really work.** It always prints `<OFX></OFX>`, which is just a placeholder marked TODO.
2. **Import silently skips bad rows.** The sample CSV has 3 rows but only 2 get imported: the row with amount `abc` is dropped with no warning. Also, the "USD only" check runs after the file has been read rather than before.
3. **The tests read the real ledger, `data/ledger.json`.** Running `add`, `import` or `migrate` on it will make `tests/test_report.py` fail. `migrate` makes all categories lower-case (`Food` becomes `food`), and the tests expect capitals. The tests also only work when run from the repo root.
4. **`migrate` changes the ledger every time it runs.** It has no record of whether it has already been applied. Running it twice does no harm today, but that won't hold for future migrations.
5. **Commands with missing arguments crash.** For example, `budget.py report` with no month gives a Python error instead of the usage message.