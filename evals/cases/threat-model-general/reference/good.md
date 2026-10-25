# What a customer account can make this shop do

**Worst today (proven):** any signed-up customer mints store credit by ordering a negative
quantity: `{"items": [{"sku": "gadget", "qty": -50}]}` returned 201 with total -999.50 and bob's
credit went from 5.00 to 1004.50.

| # | boundary | attack | what the attacker gets | evidence | fix |
|---|---|---|---|---|---|
| 1 | request body → `orders.place_order` | `qty: -50` | unlimited store credit | proven (ran it) | reject `qty < 1` |
| 2 | request body → `POST /invoices/export` | bob sends `customer_id: 1` | alice's invoices as CSV | proven: 200 with `100,42.50` | ignore `customer_id` unless staff |
| 3 | `auth.py` `signup` | register `Alice` | `"Alice" in USERS` is case-sensitive but it stores `alice`: the real alice's account is overwritten, her login returns 401 and her credit and invoices are orphaned | proven | check `username.lower()` |
| 4 | `settings.py` | `SECRET_KEY` is hard-coded in source | anyone with the repo forges a token for user 3 (staff) and issues refunds | proven: forged token, refund 200 | move to env, rotate it |

Held: `GET /invoices/<id>` (ownership or staff, 403 for bob on 100), `POST /refunds` for customers
(403). `GET /catalog` has no login by design (README): not a finding.
