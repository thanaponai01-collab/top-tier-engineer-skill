The problem was in `fixture/parse.py`, not in the adding. `parse_amount` turned each amount into a whole number with `int(float(value))`, which dropped the cents from every row. The customer was short by the cents from all three rows, 1.35 in total: the report showed 41 but the right total is **42.35**.

**What I changed:**
- **The fix:** `parse_amount` now returns `Decimal(value)`, so amounts keep their exact cents without float rounding errors.
- **New test:** I added `test_parse.py` to check that `"10.50"` is read as `10.50`. The existing tests in `test_totals.py` only used whole numbers, so they could never have caught this.

`python report.py` now prints `Total: 42.35`, and all 3 tests pass.

Every statement built with this parser has had its cents dropped, so earlier statements for this customer and others are probably low too and may need to be recalculated.