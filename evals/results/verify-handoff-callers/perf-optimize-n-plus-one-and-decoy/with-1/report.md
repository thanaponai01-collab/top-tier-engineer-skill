**The dashboard is fine for the activity feed but not for the customer table.** `customer_totals` runs one query per customer, so it grows linearly with customers. That's about 100 ms at 50k customers on in-memory SQLite, and it will be worse against a networked database. I changed nothing in `fixture/`.

**Measured (proven, in-memory SQLite, 4 orders per customer, median of 5 runs):**

| customers | `customer_totals` now | single-query rewrite | `recent_orders` |
|---|---|---|---|
| 50 | 0.1 ms | 0.0 ms | 0.01 ms |
| 5,000 | 9.5 ms | 4.3 ms | 0.02 ms |
| 50,000 | 105 ms | 48 ms | 0.02 ms |

**Findings:**

| query | growth | plan line (at 50k customers) | verdict |
|---|---|---|---|
| `customer_totals`, 1 + N queries (`report.py:3-9`) | unbounded: a query per customer | `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)`, run once per customer | **Finding.** Each lookup is indexed and fast, but there are N of them. Over a network, N round trips of about 1 ms each would take tens of seconds. |
| `recent_orders` (`report.py:15-18`) | flat, bounded by `limit` | `SCAN orders USING INDEX idx_orders_created_at` | Fine. The index supplies the order, so it stops after `limit` rows. The "SCAN" here is a walk of the index and stops early. |

**Fix (traced):** fetch everything in one query.

```sql
SELECT c.name, COALESCE(SUM(o.total), 0.0)
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id
```

- **Plan:** `SCAN c` followed by `SEARCH o USING INDEX idx_orders_customer_id (customer_id=?) LEFT-JOIN`. That is one statement and one round trip.
- **Same results:** the output matched the current function exactly at all three sizes. Customers with no orders still get 0.0.
- **No new index or migration:** the existing `customer_id` index already covers it.

**What the fix doesn't solve:**
- **Still grows with the table:** the join still touches every customer and order, so it grows with the table. It is about 2× faster here and removes the per-customer round trips.
- **Unbounded dashboard payload:** a dashboard table that returns tens of thousands of rows is a problem in itself. It needs pagination or a top-N, or a maintained per-customer totals table if you need all rows. That's a product decision, so I haven't made it.
- **Customer names as keys:** the function keys results by `name`. If two customers share a name, one silently overwrites the other. I left this as is, but it's worth checking before onboarding a chain.
- **Test data is small:** the 4 orders per customer is also from the fixture seed. A chain with long order histories will make the aggregate heavier.

**Not run:** the numbers come from in-memory SQLite. I haven't checked your production engine, so rerun `EXPLAIN` there, since plans can differ.

Want me to apply the rewrite and add a guard test? The guard would count queries or time 5,000 customers.