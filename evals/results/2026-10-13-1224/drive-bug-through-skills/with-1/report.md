Fixed and checked: `python report.py` now prints `Total: 42.35` (it was 41).

**Cause.** `parse.py:6` read each amount with `int(float(value))`, which threw away the cents. 10.50 + 20.25 + 11.60 became 10 + 20 + 11 = 41. The adding in `totals.py` was fine. The existing tests only used whole numbers, so they never caught this.

**Fix.** `parse_amount` now returns `Decimal(value)`. That keeps the cents exactly, with no float rounding error. It's a two-line change in `parse.py`.

**How I know it works** (run through the drive helper; `RUN.json` status is complete):
- `diagnose.py` checks that the CSV itself adds up to 42.35 and that parsing 10.50 doesn't lose the cents. Before the fix it failed with `parsed 10.50 -> 10`; now it passes.
- `acceptance.py` runs the real `python report.py` and requires exactly `Total: 42.35`. Before the fix it failed with `Total: 41`; now it passes.
- The two existing unit tests in `test_totals.py` still pass.
- `finish` re-ran all three against the final code and they passed.

I added `acceptance.py`, `diagnose.py` and `RUN.json` in `fixture/`, and `contract.json` one level up.

**Still open:**
- Amounts are printed as they appear in the file, so an amount written like `10.5` would print as `10.5`, not `10.50`. This data doesn't hit that. If statements must always show two decimals, `report.py` would need to format the total.
- Every customer total produced before this fix was short by the cents that were dropped. Past statements may need re-issuing.