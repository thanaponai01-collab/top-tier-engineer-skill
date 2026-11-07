The cleanup is finished. All 7 tests passed before and after, and the helper's final check passed. There was no record from an earlier cleanup, so there's nothing to report as "came back since last time". Besides the tests, I ran `list`, `report`, `export csv/qif/ofx` and `import`; for `import` I put the ledger back afterwards.

**Removed**
- `app/report_old.py`: an old copy of the report module that nothing imports.
- `test_fix.py`: a scratch script that printed two totals and checked nothing.
- `debug_output.txt`: pasted debug output.
- `IMPLEMENTATION_SUMMARY.md`: an agent's change log, and it was misleading (see the January total below).
- `app/settings.py`: a second config reader that did the same job as `app/config.py` but was written differently. `importer.py` now uses `config.load_config()`.
- Three identical money formatters (`fmt_money` in `export.py`, `_fmt` in `report.py`, and `money.format_money`) are now one: everything uses `money.format_money`.
- From `report.py`: two functions nothing calls (`legacy_totals`, `summary_line`), the unused imports `json` and `os`, and a "fixed the rounding bug" change-log comment.
- From `export.py`: a commented-out old CSV exporter.
- From `importer.py`: the unused `import re`.
- From `store.py`: a `print("DEBUG loaded …")` that printed on every command.
- Stale `__pycache__` folders.

**Fixed a bug (this changes what the program does)**
- `report.monthly_total` returned a hard-coded `123456` for January 2026. For every other month it added up the size of each amount, ignoring the minus sign, so refunds were added instead of subtracted. The hard-coded number only hid this, and only for January. It now adds amounts with their signs. January still comes out to 123456, because that is the real total. But any other month with a refund will now show a lower total than before.

**Kept, though it looked like mess**
- `app/migrate_v2.py`: its name looks like a leftover version, but `config.json` names it and `budget.py migrate` loads it by that name.
- `scripts/backfill.py`: no code calls it, but the README tells people to run it.
- `app/formats/qif.py` and `ofx.py`: nothing imports them directly, but `export qif` and `export ofx` load them by name.
- `.cleanup/`: the next cleanup run compares against it.

**Found, not changed**
- **Import quietly drops bad rows.** In `app/importer.py:14` there's an `except Exception: pass`. With `data/sample_import.csv`, the row `Transport,abc` is skipped without any warning, and the output just says "imported 2 rows". Skipping may be intended, but at the least it should report what it skipped.
- **The import currency check is in the wrong place.** In `importer.py` it runs only after the whole file has been read. It should probably happen first.
- **OFX export is a placeholder.** `app/formats/ofx.py` always returns `<OFX></OFX>`.
- **The tests leave things uncovered.** Export, import and migrate have no tests. Only January and February totals are tested, so the refund bug above was never caught.

<!-- file written by the agent: fixture/.cleanup/candidates.md -->
# Cleanup candidates

Leads, not verdicts: read each before you act. Swallowed errors, stubs and
hard-coded answers change behavior when fixed; say so if you fix one.

## leftover-version (1)
- app/migrate_v2.py  migrate_v2.py

## stub (1)
- app/formats/ofx.py:5  # TODO: implement real OFX output

## swallowed-error (1)
- app/importer.py:14  except: pass
