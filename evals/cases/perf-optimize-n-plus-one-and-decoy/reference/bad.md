# Perf Optimize — fixture/

Looked at both queries in `report.py`.

`customer_totals` runs a query per customer, but each one is indexed on `customer_id`, so it's
acceptable because each lookup uses the index — fast per call, and with 50 customers today it's a
non-issue.

`recent_orders` is more concerning: `ORDER BY created_at DESC` sounds like it sorts the whole
`orders` table on every call, and that will get worse as order volume grows. Recommend adding an
index on `created_at` before this ships to more customers.

No other findings.
