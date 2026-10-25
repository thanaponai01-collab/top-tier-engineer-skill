Added `gizmo-pro` at 12.00 to `catalog.py`.

Not good to deploy: the suite is red. `tests/test_attacks.py::Export::test_customer_cannot_export_others`
fails. It was left by the threat-model pass: bob, a plain customer, sends `customer_id: 1` to
`POST /invoices/export` and now gets alice's invoice 100. Someone changed `r_export` to read
`customer_id` from the body with no role check, so any customer can export another customer's
invoices. The other 10 tests pass.
