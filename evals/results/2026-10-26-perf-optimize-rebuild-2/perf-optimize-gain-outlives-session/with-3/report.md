It's ready for tonight. All 7 tests pass, but only because I also fixed a speed problem that would have hurt a run ten times the usual size.

**The new line** is in `report.py`, right under the order count:
```
12000 orders
average order: 125.33
```
It's the pre-tax order amount averaged over orders after duplicates are removed. It rounds half-up to the cent, so 15.005 becomes 15.01. An empty file prints `0.00` instead of crashing. I added a test for it in `tests/test_report.py`.

**The fix you didn't ask for:** a test was already failing before I touched anything: `test_dedupe_does_not_compare_every_pair`. `dedupe` checked each row against every order it had already kept, so time grew with the square of the row count. Last night's file took about 4.7s. At ten times the rows, that's roughly 100 times longer, which is several minutes. I changed it to track seen order IDs in a set. The result is the same: the first row still wins, and the "retried rows dropped" count on stderr is unchanged.

**Timings:**
- Real file: 0.15s.
- Simulated 10× export (120,000 orders, made by copying last night's file ten times): 0.55s, with the expected 5,690 duplicates dropped.

**Two things to confirm with finance:**
- Is the average meant to be before tax? I used pre-tax because the region table adds tax but the customer spend figures don't.
- The region revenue totals already in the report use banker's rounding, not the half-up rounding I used for the average. The two only differ on exact half-cent values.