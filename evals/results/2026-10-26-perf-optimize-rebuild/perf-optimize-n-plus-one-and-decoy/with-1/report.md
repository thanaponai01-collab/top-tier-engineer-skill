I only diagnosed. Nothing in `fixture/` was changed, since you asked what will happen, not for a fix. **`customer_totals` is an N+1 query and will be the problem. `recent_orders` is fine.**

**What I ran:** a workload in `scratch/workload.py` that builds the real schema, seeds N customers with 4 orders each, runs both widgets, and counts every SQL statement. I timed it with the skill's helper at 5,000 and 50,000 customers, and also ran it at 50 to match today's setup.

| Customers | `customer_totals` queries | `customer_totals` time | `recent_orders` queries | `recent_orders` time |
|---|---|---|---|---|
| 50 | 51 | 0.2 ms | 1 | 0.05 ms |
| 5,000 | 5,001 | 15.8 ms | 1 | 0.20 ms |
| 50,000 | 50,001 | 181 ms | 1 | 0.14 ms |

The whole workload took a median of 0.201s at 5,000 (range 0.186–0.224s, 5 runs) and 0.831s at 50,000 (0.812–0.959s). That total includes seeding and Python startup. The helper therefore reports the total growing 4.1x for 10x the input, but the dashboard function on its own grew about 11x. In the profile at 50,000, `customer_totals` took 26% of all time: 50,000 `execute` calls and 50,000 `fetchone` calls. `recent_orders` was about 0%.

**Why:**
- **`customer_totals`** (`report.py:3-9`) fetches every customer, then sends one `SELECT SUM(total) … WHERE customer_id = ?` per customer. So it sends one query per customer plus one, and that grows with the customer count. Each of those queries does use the index (`SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)`), so the index isn't the problem; the number of round trips is.
  - The 181 ms is the best case: in-memory SQLite, no network. Against a database server about 1 ms away, 50,000 round trips is roughly **50 seconds per page load**. That last figure is an estimate; I didn't run it against a server.
- **`recent_orders`** is a single query that reads the newest rows straight off the date index (`SCAN orders USING INDEX idx_orders_created_at`, stopping after the limit). Its time stayed flat as the data grew.

**The fix, if you want it:** replace the loop with one query, `SELECT c.name, COALESCE(SUM(o.total), 0.0) FROM customers c LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.id`. That cuts the query count from N+1 to 1 and keeps customers with no orders at 0.0. If I make that change, I'll show it returns exactly what it returns now and add a test that fails if the query count rises again. Separately, the table will have 50,000 rows, so you may want pagination or a limit regardless.

**Not measured:**
- A real networked database, or whatever database you run in production.
- Many orders per customer (I used 4 each).
- Many dashboards loading at the same time.
- Anything above 50,000 customers.
- `db.seed`'s row-by-row inserts, which are slow at this size but only fill test data.

The `.perf/` working folder is deleted. `scratch/workload.py` is still there if you want to re-run the numbers.