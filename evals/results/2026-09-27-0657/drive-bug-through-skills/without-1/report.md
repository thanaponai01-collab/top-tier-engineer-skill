The statement total is fixed: `python report.py` now prints `Total: 42.35` instead of `Total: 41`.

**Cause:** the bug was in `parse.py`, not in the adding. `parse_amount` did `int(float(value))`, which dropped the cents from every row, so 10.50 + 20.25 + 11.60 was added up as 10 + 20 + 11 = 41. The customer was short 1.35. The existing tests didn't catch it because they only check `total()` with whole numbers, and `total()` was never wrong.

**Fix:** `parse_amount` now reads amounts with `Decimal` instead of `float`, so cents are kept exactly. With `float` you can get results like `0.1 + 0.2 = 0.30000000000000004`, which you don't want on a statement.

**How I know it's fixed:**
- I added `test_report.py` with three tests:
  - one row keeps its cents;
  - the full report on `data.csv` prints exactly `Total: 42.35`;
  - 0.10 + 0.20 prints `Total: 0.30`, checking for float rounding errors.
- All 5 tests pass (the 3 new ones and the 2 existing ones).
- I temporarily put the old parsing back, and all 3 new tests failed, so they do catch this bug. Then I restored the fix.

One thing to know: the total now shows cents as written in the CSV (e.g. `42.35`). If some rows have one decimal place and others two, it will show the longest (a total of 5.5 would print as `5.5`, not `5.50`). If statements need to always show two decimal places, that's a one-line change in `report.py`.