# Root cause — fixture/

**The cents are gone before anything is added up.** `parse.py`, in
`parse_amount`, runs the field through `int(float(...))`. 12.50 becomes 12. The
sum is then perfectly correct about the wrong numbers.

Proven in both directions, not observed once:

- With the cause in place: `report.py` prints `Total: 41`, and the parsed rows
  come back as whole units.
- With the truncation removed and nothing else touched: the same run prints
  42.35, the figure the CSV actually holds. Put it back and 41 returns.

Why the suite never saw it: `test_totals` builds its rows in the test file from
whole-number amounts and never calls into `parse.py` at all. It exercises the
adding, which was never broken. No test in this tree runs a real CSV field
through the parser, so the one function that loses data has no coverage.

`report.py` and `totals.py` are where the wrong figure becomes visible. Neither
is where it is made, and rounding at the point of display would hide the loss
rather than undo it — the cents are already gone by then.
