**The dashboard's customer table will get slower in proportion to customer count. The activity feed won't change.** I only measured and changed nothing. All numbers are from an in-memory SQLite database with 4 orders per customer, run here (proven).

| Customers | `customer_totals` (median of 5) | `recent_orders` |
|---|---|---|
| 50 | 0.1 ms | 0.02 ms |
| 5,000 | 9.6 ms | 0.02 ms |
| 20,000 | 40 ms | 0.02 ms |
| 50,000 | 104 ms | 0.02 ms |

**Findings**

| Query | Growth | Plan line (50k customers) | Verdict |
|---|---|---|---|
| `customer_totals` (`report.py:3-9`) | Unbounded: one query per customer (N+1) | `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)` | **Finding.** Each lookup is indexed, but it runs N times and the whole dict is built in Python. |
| `recent_orders` (`report.py:15-19`) | Flat | `SCAN orders USING INDEX idx_orders_created_at` | Fine. With `LIMIT`, it reads the index in order and stops after 20 rows. |

**Where this matters most:** my 104 ms is the cheap case, because SQLite runs in-process and each query costs microseconds. If your production database is on the network, each of those N queries is a round trip of about 0.5–2 ms. At 30,000 customers that is roughly 15–60 seconds per dashboard load (suspected, not measured). It would also hold a connection for that whole time.

**Fix**
- Replace the loop with one query:
  ```sql
  SELECT c.name, COALESCE(SUM(o.total), 0.0)
  FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
  GROUP BY c.id
  ```
- I ran this at 50k customers. It took 47 ms, about 2x faster, and returned a dict equal to the current output (proven). Its plan is `SCAN c` plus `SEARCH o USING INDEX idx_orders_customer_id (customer_id=?) LEFT-JOIN`. It makes one round trip instead of N.
- The join still touches every customer, so the cost still grows with customer count. At tens of thousands of customers the table needs pagination (or search plus `LIMIT`) rather than rendering every customer. A dashboard table showing 50k rows is also a UI problem.
- If it has to show everything, a precomputed per-customer totals table would avoid summing orders on every load. That needs a decision on how fresh the numbers must be.
- No new index is needed: `customer_id` is already indexed. The `LEFT JOIN` and `COALESCE` keep customers with no orders at 0, as today.

**Limits of this check**
- The seed data is uniform, with 4 orders per customer. Real chains will have skewed data, so re-run on production-shaped data.
- The tests only cover 50 customers, so they wouldn't catch this. I'd add a guard that counts queries or asserts `customer_totals` stays flat as customers grow.
- `customer_totals` keys its result by `name`. Two customers with the same name would silently merge into one row. That's unrelated to performance, but a chain is likely to have duplicates.

Want me to apply the join, add a scaling test, and re-measure? Pagination would be a separate decision.