The activity feed will be fine at that size. The spend table will get slow, and before you even get to speed, it will show wrong numbers for this chain.

I seeded the fixture at 50, 5,000 and 50,000 customers (4 orders each) and timed both functions. I didn't change anything in `fixture/`.

| customers | `customer_totals` | queries issued | one-query version | `recent_orders` |
|---|---|---|---|---|
| 50 | 0.1 ms | 51 | 0.1 ms | 0.02 ms |
| 5,000 | 12.6 ms | 5,001 | 5.6 ms | 0.11 ms |
| 50,000 | 125 ms | 50,001 | 58 ms | 0.17 ms |

## 1. Totals are keyed by customer name, so customers with the same name get merged (correctness)
`report.py:9` does `totals[name] = ...`. When two customers share a name, the second one silently overwrites the first. I tested two customers both named "Main St" with spend of 100 and 50. The function returned `{'Main St': 50.0}`, so 100 of spend vanished with no error. A chain is very likely to have repeated names like store or branch names. Your current test customers are all named `customer-{id}`, which is why the tests never catch this. **This is the one to fix before onboarding.** Key the result by `id` and carry `name` along as a field.

## 2. `customer_totals` runs one query per customer (scaling)
It fetches every customer, then runs a separate `SUM` query for each one (`report.py:5-8`). The `customer_id` index makes each query cheap, so cost grows in a straight line with the number of customers. The 125 ms figure above is a best case, though: it's in-memory SQLite, where a query has no network cost. On a networked database at roughly 0.5–1 ms per round trip, 50,000 queries comes to **about 25–50 seconds per dashboard load**, on every load. A single `LEFT JOIN ... GROUP BY c.id` does the same work in one query (keep the `LEFT JOIN` so customers with no orders still show up as 0):

```sql
SELECT c.id, c.name, COALESCE(SUM(o.total), 0)
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id
```

## 3. The table returns every customer at once
Even with one query, the function still builds and sends tens of thousands of rows to a dashboard table every time it loads. Add paging (`LIMIT`/`OFFSET`, or better, paging that continues from the last row shown) and probably a sort such as top spenders first. If the chain has a lot of order history, you could also precompute the totals.

## `recent_orders` is fine
SQLite's query plan shows it reading the `created_at` index (`SCAN orders USING COVERING INDEX idx_orders_created_at`) and stopping after `LIMIT` rows. Time barely moves from 50 to 50,000 customers. One caveat: `created_at` is stored as text, so the newest-first order is only right if every timestamp uses the same ISO format and timezone. Check that the chain's imported data does.

Suggested order: fix the name keying (and add a test with two customers who share a name), switch to the single query, then add paging. I can make these changes if you'd like.