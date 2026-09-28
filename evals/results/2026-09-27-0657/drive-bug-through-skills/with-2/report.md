Fixed: `python report.py` now prints `Total: 42.35` instead of `Total: 41`. The customer's statement was short by 1.35, which is the cents dropped from each row.

**Cause:** `parse_amount` in `parse.py` did `int(float(value))`, which truncated every amount (10.50 became 10, 20.25 became 20, 11.60 became 11) before anything was added up. The adding code in `totals.py` was fine.

**Fix:** in `parse.py`, `parse_amount` now returns `Decimal(value)`. `load()` is its only caller. I used `Decimal` instead of `float` so money adds up exactly, with no results like 42.349999….

**How I know it's fixed:**
- Before any change, `load('data.csv')` returned `10, 20, 11`, which confirmed where the cents were lost.
- I added `test_report.py`, which checks that `render("data.csv")` returns `Total: 42.35`. It failed before the fix and passes after.
- All 3 tests pass, including the 2 existing ones in `test_totals.py`.

**Not checked:**
- Amounts are now `Decimal` instead of `int`. Nothing else in `fixture/` uses them, but code outside this folder that expects whole numbers would see the change.
- The total prints exactly as the data is written, with no fixed 2-decimal rounding. A value like `10.5` would show as `10.5`, not `10.50`. If statements need exactly two decimals, that's a one-line format change I can make.
- `data.csv` has no bad or empty amounts, so I haven't tested how the parser handles them.