The average line is added and all 7 tests pass. I think it's ready for tonight, but only because I also fixed a speed problem that was already in the code. That fix is a change you didn't ask for, so please look at it before the run.

**The new line**
```
12000 orders
average order: 125.33
```
- It's the average of the order amounts **before tax**, counting each order once (repeated rows from export retries are dropped first). Finance should confirm they don't want it with tax included.
- It rounds to 2 decimals the same way the revenue column already does. That method sends an exact half-cent to the even digit, so 7.505 becomes 7.50.
- An empty export shows `0.00` instead of crashing.
- I added a test for it in `tests/test_report.py`. Apart from the new line, today's report output is identical to before.

**Why it wouldn't have been ready otherwise**
Before I changed anything, one test was already failing: `test_dedupe_does_not_compare_every_pair`. The step that drops repeated orders (`report.dedupe`) checked every row against every row kept so far. That took about 5 seconds on last night's file, and at ten times the size it would take about 100 times longer, roughly 8 minutes or more. That's my estimate; I didn't run the old code on a large file.

I changed it to remember which order IDs it has already seen, which is a two-line change in `report.py`. It works the same way: the first row still wins, and the count of dropped rows still goes to stderr for ops.

**Checks I ran**
- All tests pass, including that speed check.
- Today's file now takes 0.14s instead of about 5s.
- I made a test file 10 times bigger than last night's (120,000 orders plus 5,690 repeated rows). It ran in about 0.5s with sensible numbers.

The large test file was my own copy of last night's data with new order IDs, not real export data. If tonight's file has new region codes that aren't in `data/regions.csv`, the run will still stop with a `KeyError` as before; I didn't change that. My scratch files are in `scratch/`, outside `fixture/`, and you can delete them.