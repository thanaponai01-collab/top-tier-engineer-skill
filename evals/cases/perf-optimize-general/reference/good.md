# Nightly report: 1.42 s → 0.09 s, same output

Measured on `data/orders.csv` (12,570 rows), best of 5, warm: **1.42 s before, 0.09 s after.** A
generated export ten times bigger now runs in 0.4 s; before the change it took over a minute. The
output is byte-for-byte what it printed before (diffed against a saved copy).

| cause | where | share before | change |
|---|---|---|---|
| `regions.tax_rate` calls `_table()`, which opens and parses `data/regions.csv` again for every order row | regions.py | ~1.0 s (12,040 calls) | parse the file once (`lru_cache` on `_table`) |
| `dedupe` checks each `order_id` against a growing list, so the cost is quadratic and grows a hundredfold at 10x | report.py | ~0.5 s, ~50 s at 10x | keep the seen ids in a set; still first row wins |

Not changed: `layout.table` has a comment calling it the slow part, but the profile puts it under
a millisecond — it formats 45 short rows. A dict keyed by `order_id` would have been shorter in
`dedupe` but keeps the last row's amount, and the README says the first row is the real one.

Guard: `tests/test_speed.py` counts opens of regions.csv during a report (must be 1) and times
`dedupe` on 50,000 rows (well under a second now, minutes before). Both fail with the old files put
back.
