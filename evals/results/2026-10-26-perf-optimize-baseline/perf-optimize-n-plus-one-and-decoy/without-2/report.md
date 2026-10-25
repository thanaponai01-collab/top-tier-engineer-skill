I scaled the seed data to 50 / 5,000 / 50,000 customers (4 orders each), timed both functions, and checked the query plans. My benchmark script was in a temp directory; I didn't change anything in `fixture/`.

## `customer_totals` will slow down at that scale

It makes one query per customer (`report.py:3-9`): it fetches every customer, then runs a separate `SUM` for each one.

| customers | queries per page load | time (in-memory SQLite) |
|---|---|---|
| 50 | 51 | 0.7 ms |
| 5,000 | 5,001 | 14 ms |
| 50,000 | 50,001 | 139 ms |

Those times are the best case, because this is in-memory SQLite and each query costs only microseconds. On a real database server each query costs a network round trip, often 0.2–1 ms. At 50,000 customers that's roughly **10–50 seconds per dashboard load**, and every viewer adds the same 50k queries to the database. The index on `customer_id` is used (each lookup is an index search, not a full scan), so it doesn't help: the problem is the number of queries, not how each one runs.

**Fix:** use one aggregate query. In the same benchmark it was about 2.5× faster even with no network cost, and it's always a single round trip:

```python
def customer_totals(conn):
    return dict(conn.execute(
        "SELECT c.name, COALESCE(SUM(o.total), 0) FROM customers c "
        "LEFT JOIN orders o ON o.customer_id = c.id GROUP BY c.id"
    ).fetchall())
```

## Two more problems with `customer_totals` that the 50-customer tests don't catch

- **No limit on rows.** It returns every customer. Even with a fast query, the dashboard table would get tens of thousands of rows to send and render. It probably needs pagination or a top-N with `ORDER BY ... LIMIT/OFFSET`.
- **Totals are keyed by `name`** (`totals[name] = ...`), and `name` isn't unique. A chain's locations could easily share names, and when they do, later customers silently overwrite earlier ones. You'd get wrong totals and missing rows, with no error. The current tests can't catch this because the seed names are all unique (`customer-{cid}`). Keying by `id`, or returning `(id, name, total)` rows, fixes it.

## `recent_orders` is fine

It walks the `created_at` index and stops after `LIMIT` rows: 0.03 ms at 50 customers and 0.17 ms at 200k orders. Its cost stays almost flat as data grows.

One small thing: `created_at` is stored as TEXT, so the ordering is only right if every writer uses the same ISO-8601 format and timezone. The data that comes in during onboarding should be checked for that.

**Bottom line:** fix `customer_totals` before onboarding. That means the single query, a decision on pagination, and keying by `id`. I'd also add a test with duplicate customer names. I can make those changes if you want.