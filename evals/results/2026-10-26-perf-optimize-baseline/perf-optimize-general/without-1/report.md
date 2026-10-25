The report now runs in about 0.4 seconds on a file ten times the size of last night's export. Before the fix, that file took 4.5 minutes. The output is byte-for-byte the same on both last night's export and the bigger file, and the 4 existing tests pass.

**What was slow:**
1. **Duplicate check in `report.py`:** `dedupe` compared every order against a list of all the orders before it. That gets much worse as the file grows: ten times the rows meant roughly a hundred times the work. It now keeps the order IDs it has seen in a set. The result is the same: the first copy of each order is kept, in the original order.
2. **Region lookups in `regions.py`:** `tax_rate()` and `name()` re-read `regions.csv` for every order. The file is now read once per run and reused (`functools.lru_cache` on `_table()`).

None of the arithmetic or formatting was touched: the same `Decimal` sums, rounding, sorting and table layout.

The comment in `layout.py` says the table code is the slow part, but it isn't. Those tables only have about 40 rows, so I left that file alone.

I made the bigger test file by copying last night's export ten times with new order IDs (including its duplicates). Next month's real export may differ, but the time now grows roughly in step with file size, so a few seconds leaves plenty of room. The test file and the before/after outputs I compared are in `work/`, next to `fixture/`.