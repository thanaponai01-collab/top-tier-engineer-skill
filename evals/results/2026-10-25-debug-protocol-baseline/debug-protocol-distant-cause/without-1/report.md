I fixed it: `python report.py` now prints `Total: 42.35` instead of `Total: 41`, and all 4 tests pass.

**Cause:** `fixture/parse.py:6` read each amount with `int(float(value))`, which drops the cents from every row:

| row | CSV | parsed |
|---|---|---|
| 1 | 10.50 | 10 |
| 2 | 20.25 | 20 |
| 3 | 11.60 | 11 |

So the total came out 1.35 short, at 41 instead of 42.35. `totals.py` and `report.py` were fine; they just added up the cut-down numbers.

**Changes:**
- **`parse.py`:** `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than `float` because it stores money exactly, so sums won't drift by fractions of a cent.
- **New `test_parse.py`:** checks that cents survive parsing and that the fixture total is exactly 42.35. The existing tests missed this because they only passed whole numbers to `total()` and never tested parsing.

One thing to check: the total now prints exactly as the sum comes out, with no rounding or fixed number of decimals. If statements need a set format (always two decimals, or a currency symbol), add it in `render`.