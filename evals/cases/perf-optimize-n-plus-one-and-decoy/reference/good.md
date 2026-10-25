# Perf Optimize — query scaling — fixture/

Two functions back the dashboard. One will not survive tens of thousands of customers; the other
already scales.

| query | growth | evidence |
|---|---|---|
| `customer_totals` — one `SELECT SUM(total) FROM orders WHERE customer_id = ?` per customer | unbounded (query per item) | traced |
| `recent_orders` — `ORDER BY created_at DESC LIMIT ?` | flat (indexed lookup) | proven |

**`customer_totals` (report.py):** loops over every row from `SELECT id, name FROM customers` and
fires a separate query per customer inside the loop. That's one query per item — the round-trip
count scales with the number of customers, not with the data returned. `EXPLAIN QUERY PLAN` on the
per-customer query shows `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)`, so each
individual query is cheap — but that's beside the point. This is a finding even if fast today: at 50
customers it's 50 round trips, at tens of thousands it's tens of thousands, regardless of the index
on each one. Fix: one aggregate query — `SELECT customer_id, SUM(total) FROM orders GROUP BY
customer_id` — then join the names in Python or SQL. Single query, no growth with customer count.

**`recent_orders` (report.py):** `ORDER BY created_at DESC LIMIT ?`. Quoted plan line:
`SCAN orders USING INDEX idx_orders_created_at`. That's an index-ordered scan bounded by the LIMIT,
not a full-table sort — it's fine and doesn't need a fix.

*Test:* the plan line is quoted above for both queries.
