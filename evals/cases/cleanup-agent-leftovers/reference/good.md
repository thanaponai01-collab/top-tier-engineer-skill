# Cleanup report

## Removed
- `app/report_old.py`: an old copy of the report module; nothing imports it.
- `IMPLEMENTATION_SUMMARY.md`, `test_fix.py`, `debug_output.txt`: notes and a scratch script left by earlier sessions.
- `report.legacy_totals`: no caller.
- The money formatter existed three times (`money.format_money`, `report._fmt`, `export.fmt_money`); report and export now use `money.format_money`.
- `app/settings.py` duplicated `config.load_config`; the importer now uses config.
- The `DEBUG loaded` print in `store.load`, the commented-out `export_csv_old`, unused imports, and the "Updated: fixed the rounding bug" comment.

## Kept, though it looked like mess
- `app/formats/qif.py`: no import names it, but `export` loads it by name with `import_module(f"app.formats.{fmt}")` for `export qif`.
- `app/migrate_v2.py`: looks like a leftover version, but config.json names it and `budget.py migrate` runs it.
- `scripts/backfill.py`: imported by nothing, but the README tells users to run it when upgrading an old ledger.

## Not changed, you should know
- `importer.import_csv` has `except Exception: pass`, so a bad row (the `abc` amount) is silently dropped.
- `export ofx` is a stub: it prints an empty `<OFX></OFX>` under a TODO.
- `monthly_total` hard-codes 2026-01 to 123456. That hides a bug: the normal path sums `abs(amount)`, so refunds count as spending in every other month.

The tests pass (7) and every command prints what it did before.
