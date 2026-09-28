The total is fixed. `python report.py` now prints `Total: 42.35`, which matches the CSV: 10.50 + 20.25 + 11.60.

**Cause:** `parse.py` read each amount with `int(float(value))`, which dropped the cents from every row. That made the three rows 10, 20 and 11, so the total came out 41, which is 1.35 short.

**Fix:** `parse_amount` now returns `Decimal(value)`. This keeps the cents and adds money exactly, without the rounding errors floats can introduce. `totals.py` needed no changes.

**How I checked it:**
- I added two tests to `test_totals.py`. One checks that parsing `"10.50"` keeps the cents. The other checks that `render("data.csv")` returns `"Total: 42.35"`, so it covers the whole path the customer sees.
- All 4 tests pass with the fix.
- I put the old parsing line back temporarily and reran the tests: both new tests failed. So they do catch this bug, and they would catch it if it came back.

The fix only covers future runs. Any statements already sent out with the truncated amounts will still be short and need to be checked separately.