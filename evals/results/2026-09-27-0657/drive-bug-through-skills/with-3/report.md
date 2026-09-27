I fixed it: the report now prints **`Total: 42.35`**, which is 10.50 + 20.25 + 11.60. Before, it printed `Total: 41`.

**Cause (proven both ways):** `parse_amount` in `parse.py` did `int(float(value))`, which dropped the cents from every row before they were added up. The CSV had the right values, and `total()` adds correctly. It was the cents being thrown away (50 + 25 + 60 = 1.35 in total) that made the statement short.
- With the old `parse.py` put back, the new tests fail and the report prints `Total: 41`.
- With only that line changed, the tests pass and the report prints `Total: 42.35`.

**Fix:** `parse_amount` now returns `Decimal(value)`, a two-line change in `parse.py`. I used `Decimal` rather than `float` so the money values add up exactly. `parse_amount` has one caller, `load()`, and every report goes through it, so this one change covers them all.

**What now catches it:** a new test file, `test_report.py`, with two tests:
- One runs the real report on `data.csv` and expects `Total: 42.35`.
- One checks that `parse_amount("10.50")` keeps the cents.

Both failed against the old code. All 4 tests pass now, including the 2 existing ones in `test_totals.py`.

**Why it wasn't caught:** the existing tests only give `total()` whole numbers and never run the parser, so the cents were never tested.

**Not checked:**
- **Other data:** I only tested this CSV. Amounts like `$1,000.00` or an empty field would raise an error, both before and after the fix. There's no such data here, so I left it alone.
- **Past statements:** I didn't look at statements generated before the fix. Every one of them was probably short by the dropped cents, which may be worth a follow-up with the customer.

The debug and fix steps ran as their skills. I didn't load the separate correctness-gate skill, because its check (full test suite plus running the real command) was already done above.