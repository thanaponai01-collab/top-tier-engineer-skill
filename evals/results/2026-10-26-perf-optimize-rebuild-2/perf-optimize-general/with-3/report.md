The report now runs in about half a second on an export ten times bigger. Before the change, that same 10× file took **7 minutes**, not a few seconds, so the job would have overrun the nightly window. Every figure it prints is the same as before: the gate compared the full output on both inputs and found no differences.

| Workload | Before | After |
|---|---|---|
| `data/orders.csv` (12,569 rows) | 2.14 s median (2.05–2.23, 5 runs) | 0.15 s (0.14–0.17, 5 runs) |
| 10× export (125,690 rows) | 424 s (1 run) | 0.49 s (0.48–0.51, 3 runs) |

**What was slow and the fix, one line each:**
- `regions.py::_table`: it re-read `regions.csv` from disk for every order (12,040 reads, 70% of the time). It now reads the file once per run (`functools.lru_cache`).
- `report.py::dedupe`: it checked each `order_id` against a growing *list* of IDs already seen, so time grew with the square of the row count (198× slower for 10× the rows). It now uses a set. The first row for each order still wins, as the README requires.

I didn't touch `layout.table`, even though its comment calls it "the slow part". It didn't show up in the profile; the tables it formats are tiny.

**Guard:** I added `tests/test_scaling.py`, which counts work instead of timing it. One test counts the ID comparisons in `dedupe` and the other counts reads of the regions file. The full suite passes now, and fails if either of the two edited files is put back to its old version. Run it with `python -m unittest discover tests`.

**Not measured:**
- I made the 10× file myself by copying last night's export ten times with new order IDs, keeping the duplicate retry rows. It isn't a real future export.
- All timings come from this machine. I haven't run it on the machine that runs the nightly job.

I deleted the `.perf/` working folder and my scratch data. Nothing has been committed, since this folder isn't a git repo.