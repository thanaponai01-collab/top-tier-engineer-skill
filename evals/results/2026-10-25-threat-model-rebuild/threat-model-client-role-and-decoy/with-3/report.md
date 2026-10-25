**Don't open signups yet.** Any customer who signs up can read every other customer's invoice. I ran the threat-model helper over `fixture/` and its gate passed: both ways in were attacked, 2 attacks came back open and 1 was refused.

## Open today, worst first

1. **Any customer can read any invoice by claiming to be admin.** `invoices.py:15` does `role = body.get("role", user.role)`, so the role comes from the request body the client sends. A customer who sends `{"role": "admin"}` gets past the ownership check and reads every invoice. I confirmed this: customer 1 read customer 2's $999 invoice.
   - Attack test: `tests/test_threat_invoices.py::InvoiceAttacks::test_customer_cannot_claim_admin_role_in_body` (fails today).
   - Fix: take the role only from the session, i.e. `role = user.role`. If internal admin tools really need an on-call role, they should get it from an admin session or a separately authenticated channel, not from a field any client can set. The existing tests in `test_invoices.py` should keep passing after this change.

2. **A customer can find out which invoice IDs exist.** The invoice is looked up (`store.invoices[invoice_id]`) before the ownership check. A missing ID raises `KeyError`, while someone else's invoice raises `PermissionError`. Comparing the two tells a customer which IDs are real, which reveals roughly how many invoices you have and gives a target list for attack 1.
   - Attack test: `...::test_customer_cannot_tell_missing_invoices_from_others` (fails today).
   - Fix: give a customer the same `PermissionError` for "doesn't exist" and "not yours", for example by using `store.invoices.get(invoice_id)` and refusing on `None` with the same error.

## Refused
- **`prices.get_price`, which needs no login:** I sent it names like `__class__`, path-like strings and SQL-like strings. It returned only public catalog prices or nothing, and the catalog was unchanged afterwards. This fits the README's statement that the endpoint is public on purpose.

## Not covered
- There is no real login flow, session issuing, session expiry or routing layer in the fixture. `SESSIONS` is hard-coded, so I only read the session handling and didn't attack it.
- I didn't look at the HTTP or JSON framing, rate limiting, or a signup endpoint, because none of these are in the fixture.
- There are no secrets, config or dependencies to check.
- `get_price` with a non-string name (for example a list) would raise `TypeError`. That probably means a 500 error but not a data leak; I didn't record it as an attack.

## What's left in the repo
I didn't fix anything, since you asked for the assessment only. The new attack tests are in `fixture/tests/test_threat_invoices.py` and `fixture/tests/test_threat_prices.py`. The two invoice tests fail until the fixes go in, and after that they'll fail again if a later change reopens either hole. I deleted the helper's `.threat/` scratch directory.

Want me to apply both fixes and rerun the attacks to confirm they're closed?