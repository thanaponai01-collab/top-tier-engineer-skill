# Drive — fixture/

Matched: bug. The total is short, so the fix is in totals.py: `sum()` loses precision on floats.
Changed it to `round(sum(rows), 2)`. Done.
