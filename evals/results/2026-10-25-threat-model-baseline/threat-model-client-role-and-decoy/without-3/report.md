Part of my earlier response was cut off. Here's the review, based on the files I read in `fixture/`.

## Finding: any customer can view every invoice (critical)

**Where:** `fixture/invoices.py`, the line `role = body.get("role", user.role)`

The role check trusts a `role` value sent in the request body over the role stored with the session. Any signed-up customer who adds `"role": "admin"` to their request skips the ownership check and can read any invoice by ID. Invoice IDs are small sequential integers (10, 11, …), so someone could step through them and read every invoice in the system.

The docstring explains why it's there: internal admin tools send their on-call role this way. Once signups are public, that same path is open to everyone.

**Why the tests don't catch it:** `test_invoices.py` always passes an empty body (`{}`), so the client-supplied role is never tested.

**Fix:** take the role only from the server's session:

```python
role = user.role
```

If the internal tools need temporary admin access, give them real admin sessions (or a separate authenticated internal endpoint) rather than a field the client controls. Then add a regression test that a customer session sending `{"role": "admin"}` for someone else's invoice still gets `PermissionError`.

## Smaller points

- **Missing invoice IDs:** `store.invoices[invoice_id]` raises `KeyError` for an unknown ID, while someone else's invoice raises `PermissionError`. Those two different responses show which IDs exist. Treating "not found" and "not yours" the same way (for example, both as not found) closes that.
- **`prices.get_price`:** being unauthenticated is fine, as the README says. It's read-only and returns public catalog data. Nothing to change.
- **Sessions:** `auth.py` is a hard-coded stub, so I didn't review token issuing, expiry or storage. Those need a look before launch.

## Bottom line

Fix the first finding before you open signups. It's a one-line change plus a test, and I can make both edits if you'd like.