The report now runs in about 0.4s on a 10× export, and its output is byte-for-byte the same as before.

**Timings**

| Export | Before | After |
|---|---|---|
| Last night's (12.5k rows) | 1.55s | 0.13s |
| Synthetic 10× (125k rows) | **3m 25s** | 0.41s |

The 10× case is the one that matters. The slowdown grew much faster than the file size, so the old code would have overrun the window by minutes, not seconds.

**What changed**
1. **`regions.py`**: every order re-opened and re-read `data/regions.csv` to look up its tax rate and name, about 24,000 file reads per run. The file is now read once per run and kept in memory (`functools.lru_cache` on `_table()`).
2. **`report.py` `dedupe`**: it checked each order ID against a growing list, so the cost grew with the square of the row count. It now uses a set. The rule is the same: exact `order_id` match, and the first row wins.

The arithmetic, rounding, sorting and table layout are untouched. The comment in `layout.py` calls the table code the "slow part", but the profile shows it isn't: it only formats about 45 output lines. I left it alone.

**How I checked**
- The output on `data/orders.csv` is identical to the original.
- I built a 10× file by copying the real export ten times under new order-ID prefixes, so the retry duplicates are still in it. The original code and the new code printed identical output on it.
- `python -m unittest discover tests` passes.

I deleted the scratch files afterwards, so the only changes in `fixture/` are those two edits.