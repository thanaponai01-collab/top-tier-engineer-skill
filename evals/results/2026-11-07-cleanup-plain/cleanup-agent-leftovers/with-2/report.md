The cleanup is done. All 7 tests passed before and still pass after. I also ran every command from the README (list, report, all four export formats, import, migrate) on a copy of the repo, and each one works. This was the first cleanup run on this repo, so there's no earlier record to compare against. The record is now in `fixture/.cleanup/`; leave it there so the next run can compare against it.

**One fix changes what the program does.**
`report.monthly_total` had `if month == "2026-01": return 123456` hard-coded. Under it, the general code used `abs()`, which counts refunds as spending: January would have come out as $1255.84 instead of $1234.56. The hard-coded value was there to make the January test pass and hide that bug. The `IMPLEMENTATION_SUMMARY.md` note calling it a "fixed rounding bug" was not true. I removed both the hard-coded case and the `abs()`. January still comes out as $1234.56, now actually calculated. Any other month with a refund now gives a lower total than before, and it is the correct one. It now matches how `by_category` already handled refunds.

**Removed**
- **Leftover files:**
  - `app/report_old.py`: an older copy of the report module, imported nowhere.
  - `test_fix.py`: a scratch script.
  - `debug_output.txt`: saved debug output.
  - `IMPLEMENTATION_SUMMARY.md`: an agent's notes, and misleading.
  - `__pycache__` folders.
- **Dead code in `app/report.py`:** `legacy_totals` and `summary_line`, both never called.
- **Old comments:** a block of commented-out code in `app/export.py` and the change-log comment above `monthly_total`.
- **Debug print:** `print("DEBUG loaded …")` in `app/store.py`. It was showing up in normal output on every command, so output is now cleaner.
- **Unused imports:** `re` in the importer, and `json` and `os` in the report module.

**Merged**
- **Config readers:** `app/settings.py` did the same job as `app/config.py`. The importer now uses `config.load_config()`, and `settings.py` is deleted.
- **Money formatting:** there were three copies. `export.py` and `report.py` had their own versions of `money.format_money`, and both now use the one in `money.py`.

**Kept, though it looked like mess**
- **`app/migrate_v2.py`:** the name looks like a leftover version, but `config.json` names it and `budget.py migrate` loads it by that name.
- **`app/formats/ofx.py` and `qif.py`:** nothing imports them directly, but `budget.py export ofx|qif` loads them by name.
- **`scripts/backfill.py`:** the README tells people to run it.

**Found but not changed**
- **OFX export doesn't work yet:** `app/formats/ofx.py` is a placeholder that always outputs `<OFX></OFX>`, and the README lists `export ofx` as if it works.
- **Import drops bad rows without saying so:** `app/importer.py` silently skips any row it can't read. With `data/sample_import.csv`, the `abc` amount row disappears and you just see "imported 2 rows". Reporting skipped rows would change the output, so I left it.
- **Import checks the currency too late:** the importer reads the whole file before checking it. That is harmless, just in an odd order.
- **The tests read the real `data/ledger.json`:** they must be run from the repo root, and editing the sample ledger will break them.

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
