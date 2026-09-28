The total was short because the cents were being thrown away. `python report.py` now prints `Total: 42.35`, which is correct.

**Cause:** `parse_amount` in `parse.py` converted each amount with `int(float(value))`, which cuts off the cents: 10.50 became 10, 20.25 became 20 and 11.60 became 11. That's how the total came out as 41. The adding step in `totals.py` was fine; the existing tests only used whole numbers, so they never caught this.

**Fix:** `parse_amount` now returns `Decimal(value)`, so amounts keep their exact cents. I used `Decimal` rather than `float` because floats can round money slightly wrong.

**Test:** I added `test_keeps_cents` to `test_totals.py`. It parses the three amounts from `data.csv` and checks that they add up to exactly `42.35`. All 3 tests pass.

Any statement produced with the old code will have lost up to 99¢ per line item, so those totals may need to be recalculated.