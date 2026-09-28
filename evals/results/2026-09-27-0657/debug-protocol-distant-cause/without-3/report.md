The customer is right: the total should be **42.35**, not 41. It's fixed, and `python report.py` now prints `Total: 42.35`.

**Cause:** `report.py` and `totals.py` were fine. The bug was in how amounts were read in `parse.py`. `parse_amount` did `int(float(value))`, which dropped the cents from every row:

| id | CSV value | parsed as |
|---|---|---|
| 1 | 10.50 | 10 |
| 2 | 20.25 | 20 |
| 3 | 11.60 | 11 |

That adds up to 41 instead of 42.35. The existing tests didn't catch it because they only passed whole numbers straight to `total()` and never went through the parsing step.

**Fix:** `parse_amount` now returns `Decimal(value)`, so the cents are kept exactly. I used `Decimal` rather than just removing the `int()`, because plain `float` can produce rounding errors in money sums.

**Tests:** I added two to `test_totals.py`. One checks that parsing keeps the cents; the other runs the whole CSV through to the report and expects `Total: 42.35`. All 4 tests pass.

**Worth checking:** this truncation would have made any total with cents come out low, not just this one. Other statements produced with this code may be wrong too.