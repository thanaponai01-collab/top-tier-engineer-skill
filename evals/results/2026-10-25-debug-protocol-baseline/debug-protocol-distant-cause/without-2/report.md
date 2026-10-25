The total was short because the cents were being dropped. It's fixed: `python report.py` now prints `Total: 42.35`, which is the correct sum of 10.50 + 20.25 + 11.60. All 4 tests pass.

**Cause:** `fixture/parse.py:6` read each amount with `int(float(value))`, which cuts off everything after the decimal point. Each row lost its cents, so the total came out as 10 + 20 + 11 = 41, which is $1.35 short. The adding-up code in `totals.py` was fine. The existing tests only used whole numbers, so they never caught this.

**Fix:**
- `parse_amount` now returns `Decimal(value)`. This keeps cents exact; switching to plain `float` would introduce small rounding errors, which isn't good enough for money.
- I added `fixture/test_parse.py`. It checks that cents are kept when an amount is read, and that the report total comes out as `42.35`.

Any statement produced with this code was short by the cents on each line, so other customers may have been affected too, not just this one.