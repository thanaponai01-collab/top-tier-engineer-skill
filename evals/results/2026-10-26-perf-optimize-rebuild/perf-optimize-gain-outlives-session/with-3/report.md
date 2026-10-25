It's ready for tonight. The average line is in and all 7 tests pass, but only because I also fixed a slowdown that would have hurt tonight's run.

**The average line.** `report.py` now prints the average directly under the order count:
```
12000 orders
average order: 125.33
```
It's the pre-tax `amount` averaged over the orders left after duplicates are removed, rounded to the cent. Nothing else in the output changed. I added a test for it, and if there are no orders the line says `n/a` instead of crashing.

**The slowdown.** Before my change, one existing test was already failing: `test_dedupe_does_not_rescan_seen_ids`. It was failing for a real reason. When removing duplicate orders, `dedupe` compared each row against every row it had already kept, so the work grows with the square of the file size. Last night's 12,000 rows took about 5 seconds. At ten times the rows, that would have been roughly 100 times longer, around 8 minutes or more. I changed it to look up order IDs it has already seen. Behaviour is the same: the first row still wins and the count of dropped rows still goes to stderr.

**Verification:**
- Last night's file now runs in 0.15s instead of 5s. Apart from the new average line, the output is identical.
- I built a 10× file (120,000 orders, with duplicates) and it ran in about 0.5s.

**Two things to confirm with finance:**
- **Before or after tax:** I used the pre-tax amount (125.33). The revenue table includes tax, so if they want the average to match it, it's a one-line change.
- **Rounding:** halves are rounded to the nearest even cent (Python's default). If they want halves always rounded up, that's also a one-line change.