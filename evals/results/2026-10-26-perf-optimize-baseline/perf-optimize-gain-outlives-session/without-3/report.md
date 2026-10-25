It's ready for tonight, but only because of a second fix. As the code was, it would very likely have run late.

**Added (as requested):** the report now prints `average order: 125.33` on the line under `12000 orders`. It's the mean of the deduplicated orders' `amount` before tax, rounded to the cent, and shows `0.00` if there are no orders. If finance wants it with tax included, like the region revenue table, that's a one-line change. Tell me if so.

**The problem for tonight:** `dedupe` in `report.py` compared each row against every row already kept, so its run time grew with the square of the row count. I made a copy of last night's file 10 times over (125,690 rows, with retries) and timed it:

| | before | after |
|---|---|---|
| last night (12.5k rows) | 3.7 s | 0.1 s |
| 10× copy (125k rows) | **372 s for `dedupe` alone** | 0.4 s for the whole report |

I changed it to remember order IDs already seen, so each check is instant. The first row still wins, and the "retried rows dropped" count on stderr is unchanged.

**Checks:**
- All 6 tests pass: the original 4, plus 2 new ones for the average (normal rounding and no orders).
- On last night's data, the new output matches the original exactly except for the added line, and stderr is the same.

**One caveat:** I tested a synthetic 10× file, not a real large export. If tonight's file has new region codes not in `regions.csv` or other format changes, the run will fail regardless of this fix.

My test files are in `scratch/`, next to `fixture/`. You can delete that folder.