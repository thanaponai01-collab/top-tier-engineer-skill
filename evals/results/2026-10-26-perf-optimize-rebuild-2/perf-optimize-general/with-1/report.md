The report now runs in about half a second on an export ten times bigger, down from about seven minutes. The output is byte-for-byte the same at both sizes.

| Workload | Before | After | Output |
|---|---|---|---|
| `python report.py data/orders.csv` (12,569 rows) | median 2.148 s (2.126–2.213 s, 5 runs) | median 0.151 s (0.143–0.165 s, 5 runs) | identical |
| 10× export (125,690 rows, synthetic) | 425.4 s (1 run) | median 0.456 s (0.437–0.462 s, 3 runs) | identical |

The old code would not have fit your window next month. Going from today's size to 10× made it about 200 times slower (roughly n^2.3), so about seven minutes instead of a few seconds. Now the time grows roughly in line with the export, and at today's size it's mostly Python startup.

**Cause and fix (both from the profile):**
- **`regions.py::_table`** was 69% of the time. It re-read `data/regions.csv` from disk for every order: 12,040 file reads per run. Now it reads the file once and keeps the table in memory (`functools.lru_cache`). The tax rates and region names are the same values, and the tax maths in `by_region` is unchanged.
- **`report.py::dedupe`** was 24% at today's size, and it's what made the 10× run take minutes. It checked each `order_id` against a list of every order seen so far, so the work grew with the square of the row count. Now it checks against a set. Each `order_id` is still kept once, from its first row.
- `layout.py::table` has a comment calling it the "slow part", but it took under 2% of the time, so I left it alone.

**Guard:** I added two tests to `tests/test_report.py` that count work instead of timing it:
- `dedupe` must not compare every order with every other one.
- `by_region` must open the regions file at most once.

`python -m unittest discover tests` passes (6 tests). The checker confirmed the tests fail if either changed file is put back on its own.

**Not measured:**
- **The 10× file is made up.** I built it from last night's export copied ten times with new order IDs, so it has the same proportion of duplicates (569 in 12,569 rows). I deleted it afterwards. The real export next month may have a different mix of regions, customers or duplicates, but neither fix depends on that.
- **Timing conditions.** All timings come from this machine with the files already in the disk cache. I didn't time cold starts or the actual nightly server.

The working files the checker made under `fixture/.perf/` are deleted too.