# What a customer account can make this shop do

**Worst today (proven):** any logged-in customer issues refunds. As bob, `POST /refunds/100`
returned 200 and put alice's 42.50 back on her credit; bob can buy something, take delivery and
refund his own order the same way.

Why: `ROUTES` in `app.py` holds the raw `r_refund`, captured when the dict was built.
`permissions.protect` runs afterwards and only rebinds the module name `app.r_refund` to the
`staff_required` wrapper, so the router never calls the guard, and `orders.refund` has no role
check of its own. `test_refund_staff_only` passes because it calls `app.r_refund` directly, the
wrapped name, not the route.

| door | attack | result |
|---|---|---|
| `POST /refunds/<id>` | bob refunds invoice 100 | **open**: 200 |
| `POST /invoices/export` | bob sends `customer_id: 1` | held: only his own invoices |
| `GET /invoices/<id>` | bob reads 100 | held: 403 |
| `POST /orders` | `qty: -5` | held: 400 |
| `POST /signup` | `Alice` | held: taken |

Fix: put the guard where the router looks (wrap before `ROUTES` is built, or check the role inside
`orders.refund`), and test through `app.handle`. `GET /catalog` is public by design: not a finding.
