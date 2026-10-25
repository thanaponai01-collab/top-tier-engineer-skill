Query-scaling pass over `fixture/`. Verdict: `customer_totals` won't hold up at the volume being
discussed; `recent_orders` will.

`customer_totals` first pulls every customer row, then, inside that Python `for` loop, runs
`SELECT SUM(total) FROM orders WHERE customer_id = ?` once per row. That is a query per item — the
classic N+1 shape — and the number of round trips to the database scales with the number of
customers, not with anything about the query itself. I ran `EXPLAIN QUERY PLAN` on that per-customer
query and it comes back `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)`, so yes,
it's indexed — but that doesn't rescue it. Even though it's fast today at 50 rows, at tens of
thousands of customers this is tens of thousands of round trips, and no per-query index changes that
math. Rewrite it as one query: `SELECT customer_id, SUM(total) FROM orders GROUP BY customer_id`,
then map customer names onto the result. That collapses it to a single query regardless of how many
customers exist.

`recent_orders` is a different story. `ORDER BY created_at DESC LIMIT ?` plans as
`SCAN orders USING INDEX idx_orders_created_at` — it walks the index in order and stops at the
limit, it never sorts the whole table, and idx_orders_created_at already covers it. No change
needed there.
