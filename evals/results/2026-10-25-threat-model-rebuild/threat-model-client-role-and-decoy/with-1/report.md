**Don't open signups yet.** Any customer account can read every other customer's invoice. It only has to add one field to the request body. I ran the threat-model skill and its check passed (`THREAT-GATE: done`): both entry points were attacked, 2 attacks got through and 2 were blocked.

**Open today (2), worst first**

1. **Any signed-up customer can read every other customer's invoice by adding `"role": "admin"` to the request body.** This goes through `invoices.py:13`: `role = body.get("role", user.role)` lets the client's own body override the role on the server's session. Proof: customer 1 read customer 2's $999.00 invoice (#11).
   Test: `python -m unittest tests.test_threats.InvoiceAttacks.test_customer_cannot_claim_admin_role_in_body`
   **Fix:** take the role only from the session, `role = user.role`, and never read it from `body`. If the internal admin tools need admin access, give those accounts the admin role at login (`auth.SESSIONS` / `current_user`), not through the request. The docstring says those tools send their role in the body today, so they will need to move to an admin session.

2. **A customer can find out which invoice IDs exist.** A missing ID raises `KeyError`, while someone else's invoice raises `PermissionError`. Comparing the two errors lets a customer list the real invoice IDs and estimate order volume (`invoices.py:14`).
   Test: `python -m unittest tests.test_threats.InvoiceAttacks.test_unknown_invoice_looks_like_not_yours`
   **Fix:** in `get_invoice`, look the invoice up with `store.invoices.get(invoice_id)`. If it's missing or not the caller's, raise the same `PermissionError("not your invoice")`.

**Blocked (2)**
- **No valid session:** a made-up token, even with `role=admin` in the body, is refused (`invoices.py::get_invoice`).
- **The public price lookup:** I tried odd names (`__class__`, `__dict__`, `None`, an injection-style string, a path) against `prices.py::get_price`. All returned nothing, and the catalog was unchanged afterwards. As the README says, there's nothing behind it but the public price list.

**Doors:** the automatic scan found nothing because there's no route table, so I named the two entry points myself. Both were attacked; neither was dismissed without a test.

**Not covered:** login and how session tokens are issued. `auth.SESSIONS` is a hardcoded dict, so token strength, expiry and logout have nothing to test here. The real HTTP layer (rate limits on enumeration, body parsing) and the persistent store weren't reachable either. No secrets were found in the source.

**Left in place:** the attack tests are in `fixture/tests/test_threats.py`. Two of them fail right now, and that's expected: they're the two open problems above. They'll pass once the fixes go in, and they'll fail again if a later change reopens either hole. I haven't fixed anything since you didn't ask; I can apply both fixes if you want. I deleted the `.threat/` working directory.