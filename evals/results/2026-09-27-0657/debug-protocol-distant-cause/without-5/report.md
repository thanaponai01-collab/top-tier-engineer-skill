I fixed it: `python report.py` now prints `Total: 42.35`, which was 41 before.

**Cause:** `parse_amount` in `fixture/parse.py` did `int(float(value))`, which cut the cents off every row:

| id | CSV | parsed (before) |
|---|---|---|
| 1 | 10.50 | 10 |
| 2 | 20.25 | 20 |
| 3 | 11.60 | 11 |

That lost 1.35 in total, so the statement came out short. The adding in `totals.py` was never the problem.

**Fix:** `parse_amount` now returns `Decimal(value)`. That keeps the cents exact without float rounding errors. The existing tests still pass.

The tests didn't catch this because they only call `total()` with whole numbers that are already parsed. Nothing tests `parse.py` or runs a CSV through the whole report. A small test like `parse_amount("10.50") == Decimal("10.50")` would stop this from coming back. I can add one if you'd like.