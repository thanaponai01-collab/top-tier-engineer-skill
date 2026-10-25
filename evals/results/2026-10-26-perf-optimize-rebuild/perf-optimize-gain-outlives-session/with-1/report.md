I added the line and all 8 tests now pass. But the report wasn't ready for tonight as you gave it to me. One test was already failing before I changed anything, and that failure meant tonight's run would probably not have finished. I fixed it, and with that fix I'd call it ready.

**The average order line.** `report.py` now prints it straight under the count:
```
12000 orders
average order: 125.33
```
It's the mean order amount **before tax**, rounded to the cent, counting each order once (after duplicates are removed). If there are no orders it prints `0.00` instead of crashing. I added two tests for it. One thing to check with finance: the region table shows revenue *with* tax. If they want the average to include tax too, it's a one-line change.

**The problem that would have hit tonight.** `test_dedupe_does_not_compare_every_order_with_every_other` was failing before I touched anything. The duplicate check compared every order against every order already kept. That was barely noticeable on last night's 12.5k rows, but the work grows with the square of the row count. Ten times the rows means about 100 times the work: roughly 8 billion comparisons, which in Python likely means hours. I changed it to remember order IDs it has already seen. The first row still wins, and the `dedupe: N retried rows dropped` message on stderr is unchanged.

**Checks:**
- All 8 tests pass.
- The real `data/orders.csv` gives the same output as before plus the new line.
- I made a fake export 10 times the size (125,690 rows, 120,000 unique) by copying last night's data with renamed order IDs. Removing duplicates and building every section took 0.3 s. I didn't run the old code at that size, so the "hours" figure is an estimate, not a timing.

The table formatting in `layout.py` is inefficient too, but it only formats the 40-row region table and the top-5 list, so a bigger export doesn't affect it.