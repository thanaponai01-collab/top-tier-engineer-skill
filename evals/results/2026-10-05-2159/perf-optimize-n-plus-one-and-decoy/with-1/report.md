**Verdict:** The dashboard won't break at tens of thousands of customers, but `customer_totals` will grow linearly with customer count. Every customer costs one query, and the response will fill with data for all customers. I changed nothing in `fixture/`. The numbers come from a scratch script at `/tmp/scale.py`.

**Measured (proven).** In-memory SQLite, 4 orders per customer, median of 3 runs:

| customers | `customer_totals` (loop) | one grouped query | `recent_orders` |
|---|---|---|---|
| 50 | 0.1 ms | 0.0 ms | 0.02 ms |
| 1,000 | 1.9 ms | 0.9 ms | 0.02 ms |
| 10,000 | 19.5 ms | 9.8 ms | 0.02 ms |
| 50,000 | 116.9 ms | 50.1 ms | 0.05 ms |

| query | growth | plan line (50k customers, after `ANALYZE`) |
|---|---|---|
| `customer_totals`: `SELECT id, name FROM customers` | with table (full scan, unbounded) | not checked; it has no `WHERE`, so it must read every row |
| `customer_totals`: per-customer `SUM(total)` | one query per customer, N+1 | `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)` |
| `recent_orders` | flat | `SCAN orders USING INDEX idx_orders_created_at` |

- **N+1 loop (`report.py:5-9`).** Each query is an indexed lookup, so it's fast today, but the query count equals the customer count. On a real networked database each round trip costs far more than in-memory SQLite. At 50k customers that's 50k round trips per dashboard load, likely seconds rather than ~117 ms.
- **`recent_orders`.** It's flat. The plan reads the `created_at` index in order and stops at `LIMIT`. It stays flat as the table grows, and I'd leave it alone.

**Fix, once the chain is onboarded.** Replace the loop with a single `LEFT JOIN … GROUP BY` query. It uses the existing `customer_id` index, so no migration is needed (`GROUP` in `/tmp/scale.py`). The plan is `SCAN c` plus `SEARCH o USING INDEX idx_orders_customer_id (customer_id=?) LEFT-JOIN`, with one round trip. It returned the same totals as the current code on my 50k data (the `equal: True` check). In-memory it was about 2.3x faster. The bigger gain on a real database is dropping 50k round trips to 1. I did not apply it, since you asked what would happen.

**Larger problem the fix doesn't solve.** A table of 50k customers is unusable on a dashboard, and the join still computes all of them. The result also grows with customers. Consider paginating or searching by customer, or precomputing totals into a summary table. That's a product decision for you.

**Unrelated bug (traced).** `totals[name]` at `report.py:9` is keyed by name, not id. Two customers with the same name silently collapse into one entry. Real chain data will probably have duplicates, so key by id.

**Limits.**
- SQLite in-memory is not your production engine, so the absolute timings don't carry over. The query counts and growth shapes do.
- The seed data is uniform. A few very large customers would make each per-customer sum slower.
- A guard test (for example, a query-count assertion at 1,000 customers) goes in with the fix.