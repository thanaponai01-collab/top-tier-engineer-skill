The customer was right: the total was short. `python report.py` now prints `Total: 42.35`, which is 10.50 + 20.25 + 11.60.

**Cause:** in `parse.py`, `parse_amount` used `int(float(value))`, which dropped the cents from every row as it was read in (10.50 became 10, 20.25 became 20, 11.60 became 11). Those losses add up to exactly the missing 1.35. The adding-up code in `totals.py` was fine, which is why its tests passed.

**Fix:** `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than `float` because floats would bring back rounding errors on money (0.10 + 0.20 comes out as 0.30000000000000004).

**How we know it's fixed:** I added `test_report.py`, which checks:
- that parsing `"10.50"` keeps the cents;
- that the full report on the customer's figures prints `Total: 42.35`;
- that 0.10 + 0.20 prints `Total: 0.30` with no rounding error.

All 5 tests pass (the 3 new ones and the 2 existing ones). Against the old code, the report test would have failed with `Total: 41`. The old tests never read any real data, so they couldn't catch this.

**Two things to check:**
- **Display:** totals now keep the decimal places from the data, for example `42.35` or `0.30`. Totals from whole-number data still print without them (`30`). If the statement should always show two decimals, that's a one-line change in `report.py`.
- **Other statements:** this bug would have understated any statement whose amounts had cents, not just this customer's. Statements already sent may need to be checked.