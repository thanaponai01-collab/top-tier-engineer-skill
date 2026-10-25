The report now takes about 0.75 seconds on an export ten times bigger than last night's, and every figure it prints is unchanged. Before the fix, that size took 11 minutes.

| Input | Before | After | Output |
|---|---|---|---|
| Last night's export (12,569 rows) | 1.83s median | 0.30s median | identical |
| 3× (39,592 rows) | 64.3s | 0.52s | identical |
| 10× (131,974 rows) | 10m 59s (one run) | 0.73–0.83s (three runs) | identical, byte for byte |

The old time grew much faster than the input: 3× the rows took 35× as long. At next month's size it would have blown well past the nightly window.

**What was slow and what changed** (two lines of logic, found by profiling):
- **Duplicate check** (`report.py::dedupe`): to spot retried orders, it compared each order ID against every ID seen before it. That was 76% of the time at 3×, and it gets worse the bigger the file. It now remembers seen IDs in a set, so each check is instant. The first row of a retried order still wins.
- **Region table** (`regions.py::_table`): it re-read `regions.csv` from disk for every single order, 36,000 file opens at 3×. That was 23% of the time. It now reads the file once per run (`functools.lru_cache`).

The arithmetic (`Decimal` math, rounding, sorting) and the table layout are untouched. `layout.py` has a comment calling itself the slow part, but it barely showed up in the profile, so I left it alone.

**Checking the figures:**
- **Same output:** I compared before and after output at all three sizes, and they match exactly. The test inputs include retried orders whose amounts differ, so the first-row-wins rule was exercised.
- **New tests:** I added two to `tests/test_report.py`. One counts how many ID comparisons the duplicate check makes; the other checks that `regions.csv` is opened only once for 500 orders. Both pass now, and each fails if its fix is reverted (the skill's gate confirmed this). All 6 tests pass with `python -m unittest discover tests`.

**Not covered:**
- The 3× and 10× inputs are synthetic, built from last night's export with retries added, because I didn't have a real bigger export. Real ones may differ in shape.
- The "before" timings at 1× and 3× (1.83s, 64.3s) came from the skill's measurement runs. Its gate also compared old and new code alternately, and those runs read slower (1×: about 3.3s old vs 0.30s new) because my long 10× run of the old code was still using the CPU.
- The 10× "before" figure is a single run.
- Everything ran on this one machine.

The generated files and a copy of the original code are in `scratch/`, next to `fixture/`, and are safe to delete. I removed the skill's `.perf/` working folder.