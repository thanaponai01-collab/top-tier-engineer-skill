Any customer who signs up can read every other customer's invoice today. That should block the public launch. I didn't change any code, because you asked for a threat model and not fixes.

The helper's scanner found no entry points by itself, so I named both by hand: `invoices.py::get_invoice` and `prices.py::get_price`. I wrote an attack test for each one, and the gate finished with 2 attacks open and 2 held. I can't say the API is secure; I can say which attacks were run and how each came out.

**Open today, worst first**

1. **A customer can read anyone's invoice by sending `{"role": "admin"}` in the request body.** The problem is `role = body.get("role", user.role)` in `invoices.py`: the server takes the role from the client's request instead of from the session. Customer 1 sends that body for invoice 11 and gets customer 2's $999 invoice. Your existing test, `test_customer_cannot_view_others_invoice`, misses this because it always sends an empty body.
   - Test: `python -m unittest tests.test_attacks.InvoiceAttacks.test_customer_cannot_claim_admin_role_in_body`
   - Fix: take the role only from the logged-in user (`role = user.role`) and ignore the `role` field in the body. If internal admin tools really need an on-call role, give them their own admin sessions in `auth.py`, the one place that decides who a token belongs to. The normal path, where customers view their own invoices and admins view any, keeps working.

2. **A customer can find out which invoice IDs exist.** When the ID belongs to someone else, the call refuses with a permission error. When no invoice has that ID, it fails with a different error (a `KeyError`). By trying IDs one after another, a customer can count how many invoices there are and roughly how fast that number grows.
   - Test: `python -m unittest tests.test_attacks.InvoiceAttacks.test_missing_and_foreign_invoices_look_the_same`
   - Fix: in `get_invoice`, look the invoice up with `store.invoices.get(invoice_id)`. Then give "doesn't exist" and "not yours" the same "not your invoice" refusal.

**Held**
- **Fake token plus `role=admin`:** refused. The login check runs before the body is read.
- **Price lookup without logging in:** you can only get a catalog price or nothing. Odd names such as `__class__`, `__dict__`, `None` or a tuple don't expose anything else or change the catalog. This matches the README, which says the price lookup is meant to be public.

**Not covered**
- How sessions are created and checked. Tokens like `tok-customer-1` are hard-coded in `auth.py` and easy to guess. If real tokens look like that, an attacker could guess other customers' tokens. Nothing issues tokens yet, so I couldn't test this.
- Rate limiting, concurrency, config and dependencies: none exist in this code to attack.
- No secrets turned up in the source.

The new tests are in `tests/test_attacks.py` and `tests/test_price_attacks.py`. The two open attacks will fail until the fixes land, and any later change that reopens a hole will turn them red again. I deleted the helper's `.threat/` folder. I can make both fixes if you want, then rerun the attacks to show they pass, and that they fail again if the fix is reverted.