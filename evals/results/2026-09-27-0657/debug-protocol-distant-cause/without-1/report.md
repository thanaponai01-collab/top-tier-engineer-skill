I fixed it. `python report.py` now prints `Total: 42.35`, which is the correct sum of the three rows in `data.csv`.

**Cause:** the problem was in `parse.py`, not in the adding code. `parse_amount` did `int(float(value))`, which threw away the cents on every row:

| Row | In the file | Kept | Lost |
|---|---|---|---|
| 1 | 10.50 | 10 | 0.50 |
| 2 | 20.25 | 20 | 0.25 |
| 3 | 11.60 | 11 | 0.60 |

That's 1.35 missing in total, so the report showed 41 instead of 42.35. The existing tests didn't catch it because they only used whole numbers and never tested parsing.

**Fix:** `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than `float` so money amounts add up exactly, with no rounding errors. I also added a test in `test_totals.py` that checks cents are kept (`"10.50"` → `Decimal("10.50")`). All 3 tests pass.

Any statement produced with this code will have lost the cents on every line. Past statements may need to be regenerated or checked, not just this customer's.