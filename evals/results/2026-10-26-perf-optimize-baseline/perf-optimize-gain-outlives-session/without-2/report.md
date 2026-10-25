I've added the average order line and the tests pass. It's ready for tonight, but only because I also fixed a speed problem that would have made tonight's run very slow.

**The new line.** The report now starts:
```
12000 orders
average order: 125.33
```
The figure is the pre-tax amount averaged over the orders left after removing duplicate retry rows, so it uses the same orders as the count. It's rounded half-up to the cent. I added `average_order()` in `report.py` and a test covering normal rounding, half-cent rounding and an empty file. All 5 tests pass.

**The speed problem.** The step that drops duplicate retry rows compared every row against every row already kept, so run time grew with the square of the file size:
- Last night's 12.5k rows took 3.6 s.
- A 125k-row test file (last night's data copied ten times, so I didn't have the real export) was still running when I stopped it after 2 minutes. My estimate is about 6 minutes for a full run, and it would keep getting worse as exports grow.

I changed that step to remember the order IDs it has already seen. It still keeps the first row and reports the same dropped-row count on stderr. Results now:
- Last night's file: 0.12 s.
- The 10× test file: 0.4 s, with 120,000 orders and 5,690 retried rows dropped. That's exactly ten times last night's figures.

Apart from the new average line, the report output is identical to before.

**One thing to check with finance:** I assumed "average order value" means before tax. The revenue table includes tax, so if they want the average with tax, it's a one-line change.