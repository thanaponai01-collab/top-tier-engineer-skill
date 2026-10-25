# SUP-88: fixed at the shared function, both doors shut

The leak is in `invoices.export_csv`: it returns whichever `customer_id` it is given. Two doors
reach it with a body-supplied `customer_id`:

| door | who could use it | before | after |
|---|---|---|---|
| `POST /invoices/export` (app.py) | any customer | bob got alice's invoice 100 | 403 |
| `POST /integrations/accounting/pull` (integrations/accounting.py, registered at load time) | meant for staff, but any logged-in customer | bob got alice's invoice 100: the same leak | 403; staff sync still pulls |

Fix: `export_csv` now refuses a `customer_id` that is not the caller's unless the caller is staff.
`tests/test_export_access.py` attacks both doors as bob; with the original `invoices.py` put back
both tests fail, and they pass now. The owner's export and the staff pull still pass.
