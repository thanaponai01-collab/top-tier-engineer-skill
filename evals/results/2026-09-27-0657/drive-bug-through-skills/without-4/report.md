It's fixed: `python report.py` now prints `Total: 42.35`, which is 10.50 + 20.25 + 11.60. It used to print `Total: 41`.

**Cause:** `parse_amount` in `parse.py` did `int(float(value))`, which dropped the cents from every row before adding them up. `totals.py` and `report.py` were fine. The existing tests missed it because they only used whole numbers and never went through the parser.

**Fix:** `parse_amount` now returns `Decimal(value)`. I used `Decimal` rather than plain `float` so money adds up exactly (with floats, 0.10 + 0.20 comes out as 0.30000000000000004).

**How I know it works:** I added `test_report.py`, which checks three things: that the parser keeps cents, that amounts with cents add up exactly through the whole report, and that `data.csv` gives `Total: 42.35`. All 5 tests pass (the 2 that were already there plus my 3). I also briefly put the old parsing back, and all 3 new tests failed with the wrong totals (`41` and `11`), so they do catch this bug.

**Behaviour change:** the total now prints with however many decimal places the input has (`42.35`, or `11.90` if the last amount has a trailing zero). If anything downstream expects a whole number, it needs updating. Any statements already sent were short by the dropped cents and will need correcting.