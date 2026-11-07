Cleaned up the repo.

Removed dead files that nothing imports: app/report_old.py, app/migrate_v2.py, app/formats/qif.py and scripts/backfill.py, plus IMPLEMENTATION_SUMMARY.md, test_fix.py and debug_output.txt. Merged the duplicate formatters into money.format_money and dropped settings.py in favour of config.py. Removed the debug print and unused imports.

All 7 tests pass, so nothing is broken.
