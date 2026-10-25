Yes, it's ready for tonight. All 8 tests pass. The report now has the new line:

```
12000 orders
average order: 125.33
```

**It wasn't ready before this change, and the reason wasn't the new feature.** One of the existing tests was already failing: `test_dedupe_does_not_scan_every_seen_order`. To find duplicates, `dedupe` compared each row against every row kept so far, so the time grew with the square of the row count. Last night's file took 4.6s. At ten times the rows that would have been about 100× slower, roughly 7–8 minutes or more. I changed it to look up order IDs in a set. The output is identical to before apart from the new line: the first copy of a repeated order still wins, and the "retried rows dropped" count on stderr is unchanged. Last night's file now runs in 0.13s.

**Tonight's volume:** I made a test file ten times the size of last night's (120,000 orders, with 5,690 repeated rows) and ran the report on it. It finished in 0.5s and the totals looked right.

**What I changed in `report.py`:**
- Added `average_order(rows)` and printed `average order: X` on the line under the order count.
- Added a test for it in `tests/test_report.py`.

**Choices finance may want to confirm:**
- The average is **before tax** and counts each order once, so it matches the order count shown above it. If they want it with tax, that's a one-line change.
- It's rounded to the cent the same way the revenue figures already are (Python's default, which rounds an exact half-cent to the even digit). It only matters when an average lands exactly on a half-cent.
- An empty export shows `0.00` instead of crashing.