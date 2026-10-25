Yes, it's ready for tonight, but only because of a second fix you didn't ask for. Without it, tonight's run would have taken several minutes or more.

**The new line** (`report.py`): the report now prints the average directly under the order count:
```
12000 orders
average order: 125.33
```
It's the average of the orders' amounts **before tax**, counting each order once (repeat rows from export retries are dropped first) and rounded to the cent. If a file has no orders, it shows `0.00` instead of crashing. If finance wants the average with tax included, matching the revenue table, that's a one-line change. Let me know. I added a test for the new line too.

**The fix you didn't ask for:** before I changed anything, one existing test was already failing. The step that removes repeat orders took longer and longer as the file grew: **490 seconds** for 150,000 rows. Tonight's export is about 125,000 rows (10× last night's 12,570), so it would have run for several minutes or more. I changed it to keep a running list of order IDs already seen, which the test was written to expect. It still keeps the first row of each order and still prints how many rows it dropped for ops.

**Results:**
- All 7 tests pass, in 0.14 seconds (this run took 8 minutes before the fix).
- I built a pretend 10× export (125,690 rows, including repeats) from last night's data and ran the full report on it: **0.45 seconds**, with sensible output.

None of this is under version control, so there's no commit. The changes are in `report.py` and `tests/test_report.py`.