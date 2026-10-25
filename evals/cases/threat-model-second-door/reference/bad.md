Fixed SUP-88. `r_export` in app.py no longer reads `customer_id` from the body; a customer always
exports their own invoices. Added `test_export_ignores_customer_id`, which failed before the change
and passes now. `/invoices/export` is the only route that exports invoices, so the leak is closed.
