Next month's export would have run for about 7 minutes with the old code. It now takes under half a second, and the printed report is byte-for-byte the same.

| Input | Before | After | Output |
|---|---|---|---|
| Last night's export (12,569 rows) | 2.17 s (median of 5) | 0.14 s | identical |
| 10× export (125,690 rows, generated) | **425.7 s** (1 run) | 0.45 s | identical |

The old code got about 196× slower for 10× the rows (roughly n²), so it would have blown the nightly window. The new code scales in a straight line.

**Cause and fix, one line each:**
- **`report.py::dedupe`** (23% of the time, and the part that grows as n²): it checked each `order_id` against a list of every ID seen so far. It now uses a set. The first row for each order still wins, and the order of rows is unchanged.
- **`regions.py::_table`** (70% of the time today): it re-opened and re-parsed `regions.csv` for every order row, 12,040 times. It's now cached with `lru_cache` and read once per run. Nothing modifies that table, so the figures can't change.

`layout.py` has a comment calling it the "slow part", but it took under 1% of the time in the profile, so I left it alone.

**Guard:** I added a `Scaling` class to `tests/test_report.py` with two tests. One counts ID comparisons in `dedupe`; the other counts how many times `regions.csv` is opened. Counts don't flake the way timings do. The full suite passes now, and it fails if either changed file is put back to the original on its own.

**Not measured:** I built the 10× file by repeating last night's export ten times with suffixed order IDs, so it keeps the same mix of duplicates and the same 40 regions. A real export with many more distinct customers or regions wasn't tested, and neither were other machines or cold disk caches. Neither fix depends on those, though.

I deleted the scratch data and the `.perf/` working folder afterwards.