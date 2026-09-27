The total is fixed: `python report.py` now prints `Total: 42.35` instead of `Total: 41`, which matches 10.50 + 20.25 + 11.60.

**Cause:** in `parse.py`, `parse_amount` did `int(float(value))`, which dropped the cents from every row before they were added up. The adding in `totals.py` was correct; it was being given 10 + 20 + 11.

**Fix:** `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than just removing the `int()` because plain floats would bring their own rounding errors into money totals (for example, 0.1 + 0.2 ≠ 0.3).

**How I checked it:**
- I added `test_report.py` with four tests: cents are kept, no float rounding errors, the real `data.csv` totals `42.35`, and a second sample file (0.99 + 0.99) totals `1.98`.
- All 6 tests pass, including the two that were already in `test_totals.py`.
- I put the old line back temporarily and ran the new tests: all 4 failed. So they do catch this bug, and the code is restored to the fix.

The existing tests only fed `total()` whole numbers that had already been parsed, which is why they never caught this.

**Worth checking:** any statements made from data with cents came out short in the same way (by up to $0.99 per line item), not just this customer's. Also, the total now prints the exact amount, with no forced rounding to two decimals. If the source data can have more than two decimal places and the statement needs a fixed format, `report.py` should round or format it explicitly.