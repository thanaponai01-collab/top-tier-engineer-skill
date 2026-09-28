The bug is fixed: `python report.py` now prints `Total: 42.35`, not `Total: 41`.

**Cause (proven by a run):** `parse.py:5` read each amount with `int(float(value))`, which cut the cents off every row. The three rows lost 0.50, 0.25 and 0.60, which is the missing 1.35. The adding in `totals.py` was correct.

**Fix:** `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than float because floats don't store cents exactly. That function is the one place every amount is read, so `load()` and the report both pick up the change. It's a one-line change plus the import.

**How I know it holds:**
- I added `test_report.py`, which checks that the report shows `Total: 42.35` for `data.csv`. It failed before the fix (41 vs 42.35) and passes after.
- All 3 tests pass, including the two existing tests in `test_totals.py`.

**Not checked:**
- The customer's actual statement data. I only tested against `fixture/data.csv`.
- How the total looks when the input isn't written with two decimals. `Decimal` keeps the input's own form, so amounts like `10.5` or `10` would show as `10.5` or `10` rather than `10.50`. If statements must always show two decimals, `render` needs a format.
- The existing `test_totals.py` tests only use whole numbers, which is why they never caught this.

I did the debug, fix and test steps directly rather than loading each sub-skill, since the cause was clear from the first run.