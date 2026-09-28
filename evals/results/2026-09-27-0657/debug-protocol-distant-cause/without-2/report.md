The bug was in `parse.py`, not in the totals code, and it's fixed: `python report.py` now prints **`Total: 42.35`** instead of `Total: 41`.

**Cause:** `parse_amount` in `parse.py` did `int(float(value))`, which cut the cents off every amount before anything was added up (10.50 → 10, 20.25 → 20, 11.60 → 11). `totals.py` was adding correctly. The existing tests didn't catch this because they only pass whole numbers straight to `total()` and never go through the parser.

**Fix:**
- `parse.py`: `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than `float` because float would give `42.349999…`; `Decimal` keeps money amounts exact.
- `test_totals.py`: added `test_keeps_cents`, which loads `data.csv` through the parser and checks the total is `42.35`. All 3 tests pass.

Any other code that calls `load()` will now get `Decimal` amounts instead of ints. Nothing else in `fixture/` depends on that.