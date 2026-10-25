The activity feed will be fine at that size. The customer spend table won't be: it runs one database query per customer, so a chain with 50,000 customers means about 50,001 queries every time the dashboard loads. I only measured; nothing in `fixture/` was changed.

## Measured
I ran it on the fixture's in-memory SQLite, with 4 orders per customer. Times are the best of 5 runs, for each widget on its own:

| Customers | `customer_totals` | queries it sends | `recent_orders` |
|---|---|---|---|
| 50 | 0.1 ms | 51 | 0.015 ms |
| 5,000 | 12 ms | 5,001 | 0.016 ms |
| 50,000 | 172 ms | 50,001 | 0.017 ms |

I also timed the whole workload end to end, including Python startup and loading the test data. It took 0.14 s at 50 customers, 0.22 s at 5,000 and 0.87 s at 50,000. At 50,000, the profile puts `report.py::customer_totals` at 26% of that time, with 50,006 `execute` calls and 50,000 `fetchone` calls. The helper reported that this total grew only 6.3× for a 1000× bigger input. That's because startup and loading the data dominate the total; the widget's own time grew about 1,700×.

## Causes
- **The spend table (`report.py:1`)** fetches every customer, then sends a separate `SELECT SUM(total) … WHERE customer_id = ?` for each one. Each of those lookups uses the index (`SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)`), so the index is not the problem; the number of queries is.
  - **Why 172 ms understates it:** here every query is a cheap call inside the same process. On a database server, each query is a network round trip. At an assumed 0.5–1 ms each, 50,000 of them would take roughly 25–50 seconds per page load. I didn't measure this; it's an estimate.
  - **The fix:** a single `LEFT JOIN … GROUP BY` query. In the same test it took 77 ms at 50,000 customers, compared with 172 ms. On a server it would also replace 50,000 round trips with one.
  - **It also returns every customer to one dashboard table** (50,000 rows). It probably needs paging or a top-N limit as well, whatever the query looks like.
- **The activity feed (`recent_orders`) scales fine.** Its plan is `SCAN orders USING INDEX idx_orders_created_at`. It reads the index from the newest end and stops after `LIMIT`, so it took about 0.016 ms at every size.
- **A correctness bug to fix at the same time:** the results are keyed by customer `name` (`totals[name] = …`). If two customers share a name, one silently overwrites the other in the table. That's unlikely with ~50 test customers and quite likely with tens of thousands. The results should be keyed by `id`.

## Not measured
- A real server database and its network latency, which is where the real cost of the many queries lies.
- More than 4 orders per customer, more than 50,000 customers, and a cold cache.
- How the dashboard front end copes with a 50,000-row table.

If you want me to make the change (the single query, keying by `id`, and a test that counts queries so the per-customer version can't come back), say so. The measurement script is in `scratch/bench.py` and takes the customer count as its argument. I deleted the helper's `.perf/` folder afterwards.