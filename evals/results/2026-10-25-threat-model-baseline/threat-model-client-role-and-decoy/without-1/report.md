Looking at the code, here's what a customer account could be made to do once public signups ship.

## Critical: privilege escalation via client-supplied `role` (invoices.py:15)

```python
role = body.get("role", user.role)
...
if role != "admin" and invoice.owner_id != user.id:
```

The authorization check trusts a `role` field taken from the **request body** — data the client controls — instead of from the authenticated session. Any logged-in customer can view **any** invoice (and anyone else's billing data) just by adding `{"role": "admin"}` to their request:

```python
get_invoice("tok-customer-1", 11, {"role": "admin"}, store)  # returns invoice 11, owner_id=2
```

The existing test `test_customer_cannot_view_others_invoice` passes only because it sends `{}`. The bypass is never tested.

**Why it matters for public signup:** today `SESSIONS` holds two hand-made customer tokens. Once signups are public, anyone can get a valid `tok-*` session for free — and that session is all the attacker needs. The `role` override turns every self-service account into an admin for read purposes. This is an IDOR + privilege-escalation combined.

**Fix:** authorize off the session only. Delete the body-role path.

```python
user = current_user(session_token)
if user is None:
    raise PermissionError("not authenticated")
invoice = store.invoices[invoice_id]
if user.role != "admin" and invoice.owner_id != user.id:
    raise PermissionError("not your invoice")
return invoice
```

If internal admin tools genuinely need to act as admin, that must come from a separately-authenticated service credential, not a field any client can set. Add a regression test that asserts `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` raises `PermissionError`.

## Secondary observations

- **invoices.py:16 — `store.invoices[invoice_id]` raises `KeyError`** on a missing/invalid id. Before the ownership check, so an unauthenticated-vs-nonexistent distinction leaks, and it's an uncaught crash on bad input. Return a clean "not found" (and ideally make "not found" and "not yours" indistinguishable so IDs can't be enumerated).

- **prices.py — public by design.** The README's claim holds *only* as long as the catalog stays static reference data. `get_price` is a safe read of a constant dict. Flag it to revisit if pricing ever becomes per-customer, promotional, or writable — then "public, nothing to protect" stops being true.

- **auth.py — session model.** Tokens are a static in-memory dict with no expiry, rotation, or issuance flow. Fine for a fixture, but public signup needs real session issuance, expiry, and revocation. Not the shipping blocker here, but worth noting.

The one thing to fix before shipping is `invoices.py:15`. Want me to apply that change and add the regression test?