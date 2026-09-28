The customer is right: the total should be 42.35, and the report printed 41.

**Cause:** `parse_amount` in `fixture/parse.py` did `int(float(value))`, which dropped the cents from every row: 10.50 became 10, 20.25 became 20 and 11.60 became 11. The adding code in `totals.py` was fine; it was just given whole numbers.

**Fix:** `parse_amount` now returns `Decimal(value)`, so cents are kept exactly. I used `Decimal` rather than `float` so money amounts don't pick up small rounding errors.

`python report.py` now prints `Total: 42.35`, and both existing tests pass.

The tests missed this because they only check `total()` with whole numbers and never test parsing. A test like `parse_amount("10.50") == Decimal("10.50")` would have caught it; I can add one if you want.