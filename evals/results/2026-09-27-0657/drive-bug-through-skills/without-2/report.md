`python report.py` now prints `Total: 42.35` (10.50 + 20.25 + 11.60) instead of `Total: 41`.

**Cause:** `parse_amount` in `parse.py` used `int(float(value))`, which dropped the cents from every row: 10 + 20 + 11 = 41. The adding in `totals.py` was correct, which is why the existing tests passed. They only covered `total()` with whole numbers.

**Fix:** `parse_amount` now returns `Decimal(value)`, so cents are kept exactly. I used `Decimal` rather than a float because floats add small rounding errors to money amounts.

**How I know it works:**
- I added two tests in `test_totals.py`: one checks that `"10.50"` parses to `Decimal("10.50")`, and one runs `render()` on a copy of the CSV and expects `Total: 42.35`.
- All 4 tests pass with the fix.
- With the old line put back temporarily, both new tests fail, so they would have caught this bug.

**One thing to check:** the total now prints however many decimal places the input has. If the statement has to show exactly two (e.g. `42.00` rather than `42`), the output in `report.py` should be formatted for that.