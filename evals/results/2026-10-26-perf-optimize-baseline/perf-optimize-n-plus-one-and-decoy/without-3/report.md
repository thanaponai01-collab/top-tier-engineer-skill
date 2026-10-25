I ran both functions at 50, 5k, 20k, and 50k customers (4 orders each). The activity feed will be fine. The customer table has one real bug and one scaling problem, and the bug matters more.

## 1. Customers with the same name get merged (data bug)

`customer_totals` keys its results by customer **name** (`report.py:9`), and names aren't unique. When two customers share a name, the later one silently overwrites the earlier one:

```
customers: (1, 'Starbucks', $100 of orders), (2, 'Starbucks', $5)
customer_totals -> {'Starbucks': 5.0}      # the $100 customer is gone
```

Your 50 test customers are all named `customer-N`, so the test data can't trigger this. Among tens of thousands of real customers, duplicate names are almost certain: common personal names, or a chain's locations sharing a brand name. Rows will disappear from the table and the counts won't add up, with no error. The fix is to key by `id` and return the name alongside it.

## 2. One query per customer (scaling)

The function fetches all customers, then runs a separate `SUM` query for each one: 50,001 queries for 50k customers. Each query uses the index, so this is a query-count problem, not a missing-index problem.

| customers | current (N+1 queries) | single GROUP BY query | `recent_orders` |
|---|---|---|---|
| 50 | 0.1 ms | 0.1 ms | 0.03 ms |
| 5,000 | 10.5 ms | 4.7 ms | 0.12 ms |
| 20,000 | 46.5 ms | 20.4 ms | 0.13 ms |
| 50,000 | 118 ms | 55 ms | 0.09 ms |

These numbers understate the problem. The fixture runs SQLite in memory, where a query costs microseconds. If production talks to a database over a network (Postgres, MySQL, etc.), every query also pays a round trip, typically 0.2–1 ms. 50k queries would then take roughly **10–50 seconds per dashboard load**, likely past request timeouts. I don't know your production setup, so that range is an estimate, not a measurement.

The fix is a single query, which I checked returns the same results:

```sql
SELECT c.id, c.name, COALESCE(SUM(o.total), 0)
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id
```

## 3. The table returns every customer at once

Even with a single query, `customer_totals` returns every customer in one go. At tens of thousands of rows, the payload size and front-end rendering become the bottleneck. The dashboard table needs pagination (`LIMIT`/`OFFSET`, or keyset pagination on `id`), and probably sorting by spend on the server.

## `recent_orders` is fine

It uses `idx_orders_created_at` to read only the newest 20 rows instead of scanning the table (confirmed with the query plan), and its time stayed flat at about 0.1 ms across all sizes. The README's claim that both columns are indexed is accurate.

## What to do before onboarding

1. Key results by `id` (correctness; do this regardless of scale).
2. Replace the per-customer loop with the single `GROUP BY` query.
3. Paginate the customer table.
4. Add a test with duplicate customer names, and a seed with thousands of customers, so these problems would show up in tests.

I haven't changed anything in `fixture/`. Do you want me to make these changes?