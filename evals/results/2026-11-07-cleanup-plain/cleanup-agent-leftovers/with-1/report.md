The cleanup is done. All 7 tests passed before and after, and the cleanup helper's final check passed. I also ran every CLI command (`list`, `report`, `export csv/json/qif/ofx`, `import`, `migrate`) and `scripts/backfill.py` on a throwaway copy of the data, so your real `data/ledger.json` was not touched. This is the first cleanup run on this repo, so there is nothing to compare against from a previous one.

## Removed
- **`app/report_old.py`**: an older copy of the report module that nothing imported.
- **`test_fix.py`** and **`debug_output.txt`**: a one-off check script and the output it printed.
- **`IMPLEMENTATION_SUMMARY.md`**: an agent's change log. It described `report_old.py` and `settings.py`, which are now gone, so it would mislead the next agent.
- **`app/settings.py`**: a second copy of `app/config.py`'s `load_config`. The importer now uses `config.load_config()`, like the rest of the app.
- **Two more copies of the money formatter**: `fmt_money` in `export.py` and `_fmt` in `report.py` were identical to `money.format_money`. Both files now use the `money` version.
- **Unused functions** `legacy_totals` and `summary_line` in `report.py`.
- **Unused imports** (`json`, `os`, `re`), a commented-out `export_csv_old`, and an outdated "Updated: fixed the rounding bug" comment.
- **A `print("DEBUG loaded ...")` in `store.py`.** It printed on every command, including `export`, so exported CSV/JSON started with a junk line.
- `__pycache__` and `.pytest_cache` folders.

## Fixed (this changes what the program does)
- **January's total was faked.** `report.monthly_total` returned a fixed `123456` whenever the month was `2026-01`. Otherwise it added up `abs(amount)`, so a refund was counted as more spending.
  - The fixed number happens to be the correct January total with the refund subtracted, so the hard-coding was hiding the bug.
  - It now adds the signed amounts for every month. This matches `by_category` and the test named "january total counts the refund". The tests pass on the real calculation now, not on the faked value.
  - Any other month with a refund will now show a lower total than before.

## Kept, though it looked like mess
- **`app/migrate_v2.py`**: the "v2" name looks like a leftover copy, but `config.json` names it and `budget.py migrate` loads it by that name.
- **`app/formats/ofx.py` and `qif.py`**: no file imports them directly, but `export` loads them by name when you run `export ofx` or `export qif`.
- **`scripts/backfill.py`**: the README tells people to run it.
- **`.cleanup/`**: the cleanup tool's record. The next cleanup run compares against it.

## Found but not changed
- **Bad import rows are dropped silently.** `importer.py` catches every error and skips the row without saying so. `data/sample_import.csv` has a row with the amount `abc`, and `import` just reports "imported 2 rows" with no warning. I'd suggest printing which rows were skipped, but you should decide.
- **OFX export doesn't work.** It returns an empty `<OFX></OFX>` and has a TODO, even though the README lists `ofx` as a working format.
- **The importer checks the currency too late.** It reads the whole file before refusing a non-USD ledger. That's harmless, but it's in the wrong order.
- **There's no git repo**, so these deletions can't be undone with version control.

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
