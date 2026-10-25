## Will the dashboard scale to tens of thousands of customers?

One widget is fine. The other, `customer_totals`, runs one database query per customer: 50,001 queries at 50,000 customers. In this test setup that's still fast, but against a real database server it will probably be the reason the dashboard gets slow.

I only diagnosed; I didn't change anything in `fixture/`. All three of the skill's checks passed. I measured on the code as it is, at 50, 5,000 and 50,000 customers with 4 orders each, using SQLite in memory as `db.py` sets it up.

**Each widget timed alone:**

| Customers | `customer_totals` | Queries it ran | `recent_orders` |
|---|---|---|---|
| 50 | 0.2 ms | 51 | 0.03 ms |
| 5,000 | 18.9 ms | 5,001 | 0.21 ms |
| 50,000 | 156.6 ms | 50,001 | 0.19 ms |

**Whole workload** (start Python, seed the data, render both widgets): median 0.148 s at 50 customers and 0.969 s at 50,000, 5 runs each. Python startup and seeding dominate that number, which is why I also timed each widget alone. In the profile at 50,000, `customer_totals` took 28% of the time and made 50,009 `execute` calls.

### Cause
- **`customer_totals` (`report.py:1`)** gets every customer, then runs `SELECT SUM(total) ... WHERE customer_id = ?` once for each one. Each lookup does use the index (plan: `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)`). The cost isn't any single query, it's how many there are. Here each query costs about 3 µs because the database is in-process. On a networked database each one is a round trip. At an assumed 0.5–1 ms per trip (not measured), 50,000 customers would mean roughly 25–50 seconds per dashboard load.
- **The fix:** one query, `SELECT c.name, COALESCE(SUM(o.total), 0) FROM customers c LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.id`. I ran it once as a reference: 72.5 ms at 50,000 customers in memory (about 2x faster). The bigger saving is going from 50,001 round trips to 1 on a real server.
- **`recent_orders` is fine.** Its plan is `SCAN orders USING INDEX idx_orders_created_at`: it walks the index from the newest end and stops after `LIMIT` rows. Time stayed flat at about 0.2 ms from 5,000 to 50,000 customers.

### Correctness problems that grow with the data
These came from reading the code and counting rows, not from timing.
- **Customers with the same name merge.** `customer_totals` keys its results by `name`. A chain with many branches under the same name (or two customers who happen to share one) would show one row, holding only the last of those customers' totals; the others would disappear. The test data never hits this because every name is `customer-N`.
- **The activity feed's order isn't fixed when timestamps tie.** It sorts only by `created_at`. At 50,000 customers, 1,785 orders share the newest timestamp. So which 20 orders appear isn't defined, and could change between loads. Sorting by `created_at DESC, id DESC` would make it stable. That's an artifact of the seed data; real timestamps tie less often.

### What I didn't measure
- A real database server (Postgres or MySQL), network latency, or a database on disk rather than in memory.
- Data shaped like the chain's: more orders per customer, or a skewed spread.
- Rendering many concurrent dashboards at once.
- The browser-side cost of showing a 50,000-row table. The widget returns every customer with no paging, which will likely need addressing on its own.

The workload script and the `.perf/` folder were temporary and I've deleted them, so `fixture/` is as I found it. If you want the fix, I can rewrite `customer_totals` as the single query, key it by customer id, and add a test that counts queries so the per-customer loop can't come back.