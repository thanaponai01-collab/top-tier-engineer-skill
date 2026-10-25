# Customer dashboard (fixture)

`report.py` backs two widgets:

- `customer_totals(conn)` — spend per customer, for the table on the dashboard.
- `recent_orders(conn, limit)` — the newest orders, for the activity feed.

`db.py` builds the schema and seeds test data. Both `orders.customer_id` and
`orders.created_at` are indexed.
