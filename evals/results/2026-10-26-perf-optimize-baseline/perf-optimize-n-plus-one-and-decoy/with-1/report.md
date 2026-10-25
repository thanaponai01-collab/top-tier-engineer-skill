## Summary

**Before:** the dashboard's spend table ran one query per customer. With 50k customers that is **50,001 statements per page load**, so the cost grows with every customer you add. **After:** it runs 1 statement no matter how many customers there are, and returns the same result. **Trade-off:** none in behaviour. Customers with no orders still show 0.0, and a new test checks that.

| Query | Growth | Plan line (EXPLAIN QUERY PLAN, 50k customers / 200k orders) | Status |
|---|---|---|---|
| `customer_totals` loop (`report.py:5-9`, old) | **Unbounded**: one query per customer | `SEARCH orders USING INDEX idx_orders_customer_id (customer_id=?)` ×50,000, after `SCAN customers` | **Fixed** (proven) |
| `customer_totals` grouped join (new) | Grows with the table: one pass | `SCAN c` → `SEARCH o USING INDEX idx_orders_customer_id (customer_id=?) LEFT-JOIN` | One query; still reads every row (see below) |
| `recent_orders` | Flat | `SCAN orders USING INDEX idx_orders_created_at` + `LIMIT`, so it stops after 20 rows | Fine as is (proven) |

**Timings** (in-memory SQLite, median of 5 runs, 4 orders per customer):

| Customers | Old loop | New join | `recent_orders` |
|---|---|---|---|
| 50 | 0.2 ms | 0.1 ms | 0.016 ms |
| 5,000 | 11.7 ms | 5.6 ms | 0.018 ms |
| 50,000 | 111.5 ms | 50.0 ms | 0.016 ms |

The in-memory numbers make the old loop look far better than it would be in production. SQLite in memory has no network round trip. On a networked database, each query typically adds roughly 0.5–1 ms, so 50k queries would be about **25–50 seconds per dashboard load**. That figure is an estimate (suspected), not measured. The real problem is the statement count, and that has dropped from 50,001 to 1 (proven).

## What changed (`fixture/`)
- `report.py`: `customer_totals` is now one `LEFT JOIN … GROUP BY c.id`. There is no schema change and no new index; it uses the existing `idx_orders_customer_id`. At 50k customers I compared its output to the old loop's and they were identical.
- `test_report.py` has two new tests:
  - **A query-count check:** `customer_totals` must run exactly 1 statement. I ran it against the old loop and it failed with `51 != 1`; it passes on the new code.
  - **A no-orders check:** a customer with no orders gets 0.0.
- All 4 tests pass.

## Still to do before onboarding
1. **The spend table is still unbounded.** The query is now one statement, but it still reads every order and returns one row per customer. At tens of thousands of customers, the page would ship and render a 50k-row table on every load. Paginate it or show the top N with `ORDER BY 2 DESC LIMIT ? OFFSET ?`, or keep a per-customer total that updates as orders come in. This is a product decision, so I didn't make the change.
2. **An optional index if the join gets slow at real volume.** An index on `orders(customer_id, total)` would let the join get the totals without reading the order rows themselves. Adding an index to a populated table is a migration, though, not a one-line tweak:
   - Read the `EXPLAIN` plan on production-sized data first.
   - Use your database's non-locking method (for example, Postgres `CREATE INDEX CONCURRENTLY`).
   - Have the way back written down first (`DROP INDEX CONCURRENTLY …`).

   I didn't add it.
3. **Customer names are assumed to be unique.** Totals are keyed by customer name, which was also true of the old code. If the new chain has duplicate store names, rows will silently overwrite each other. Keying by `id` would be safer.

My measurement script is in `%TEMP%\perfscratch\probe.py`, outside the fixture.