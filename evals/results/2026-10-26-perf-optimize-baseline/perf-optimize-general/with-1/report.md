The 10× export now runs in **0.42 s, down from 126 s**, and the 1× export in 0.10 s, down from 1.64 s. I compared every run byte for byte against the original program's output on both inputs, and every figure it prints is unchanged. There was no trade-off: no caching across runs and no change to the arithmetic.

| metric | before | after | target |
|---|---|---|---|
| wall time, today's export (12,569 rows), median of 5 | 1.64 s | 0.10 s | — |
| wall time, 10× export (125,690 rows) | 126 s (1 run) | 0.42 s (median of 5, spread 0.41–0.43) | ≤ 3 s (my reading of "a few seconds") |
| printed output | — | byte-identical on both inputs, every run | identical |

**What changed (two changes, both chosen from the profile):**
1. `regions.py`: `_table()` reread `data/regions.csv` for every order. That was 1.6 s of the 2.3 s profiled run, from 12,040 file opens. It is now cached with `functools.lru_cache`, so the file is read once per run.
2. `report.py` `dedupe`: it checked for repeat orders by scanning a list, so its cost grew with the square of the row count. That was 0.59 s today and would have been about two minutes at 10×. It now uses a set. Order is kept and the first row still wins.

**Left alone:** `layout.py` has a comment calling it the "Slow part", but it doesn't show up in the profile at all. It only formats about 45 output lines. What remains in the profile is reading the CSV and the `Decimal` arithmetic, and the report needs both. So I stopped there: another gain would add complexity without being needed.

**Guards:** I added two tests to `tests/test_report.py`:
- One asserts that `regions.csv` is opened once per run.
- One checks that deduplicating 120k rows takes under 1 s. It takes about 0.05 s now. The 1 s limit is a wall-clock bound, so a very slow or busy machine could trip it.

All 6 tests pass. I also ran the new tests against the original code, and both catch it: the dedupe test fails at 51 s. The regions test gives an error rather than a clean failure, because the old function has no `cache_clear`.

**What the 10× figure is based on:** there is no real 10× export yet. I built a stand-in in `../scratch/orders10x.csv` by copying today's file ten times with new order IDs. It keeps the retried duplicates and changes some emails so the top-customers list differs. The measurements were warm-cache, single process, Python 3.13.4 on this machine. The original code's 10× time comes from a single run because each one takes two minutes. A real export with a different mix of duplicates or regions shouldn't change the result much, since both fixes now take time proportional to the row count.