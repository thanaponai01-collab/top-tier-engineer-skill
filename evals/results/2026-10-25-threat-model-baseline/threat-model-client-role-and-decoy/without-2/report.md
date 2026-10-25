Here's what a customer account could be made to do once signups open.

## The one that matters: any customer can read every invoice

`invoices.py:15`

```python
role = body.get("role", user.role)
```

The function trusts a `role` field sent in the **request body** and falls back to the real session role only if it's absent. A logged-in customer controls the body, so they just include `{"role": "admin"}` and the ownership check on the next lines is skipped entirely:

```python
if role != "admin" and invoice.owner_id != user.id:   # bypassed when role == "admin"
```

So `tok-customer-1` can fetch invoice `11` (owner_id 2, amount 999.00) — or any other customer's invoice — simply by claiming to be an admin. This is a textbook broken-access-control / privilege-escalation bug: authorization derived from client-supplied data instead of the authenticated session. The docstring frames this as "some internal admin tools pass their on-call role this way," but there's nothing restricting that path to internal tools; it's reachable by anyone with any valid session.

The existing test `test_customer_cannot_view_others_invoice` passes only because it sends an empty body `{}`. It gives false confidence — it never exercises the attacker-controlled path.

**Fix:** derive the role solely from the session; never from the body.

```python
role = user.role
```

If internal tools genuinely need role impersonation, that belongs behind a separate authenticated/privileged channel, not a field any client can set. I'd also add a regression test asserting that `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)` still raises `PermissionError`.

## Worth noting, lower priority

- **`store.invoices[invoice_id]`** (`invoices.py:16`) does a raw dict lookup. An unknown `invoice_id` raises `KeyError` rather than a clean "not found," and the lookup happens *before* the ownership check — so error behavior can differ for existing vs. non-existing IDs, a mild enumeration/oracle and a crash-on-bad-input issue. Look up first, return a not-found error uniformly, then authorize.

- **`prices.get_price`** being public is fine as documented — it's a static catalog mirror with no secrets and no user input reaching anything sensitive. No action needed; I'm flagging it only so it's a deliberate decision on the record, not an oversight.

- **Session model** is a hardcoded in-memory dict with guessable tokens (`tok-customer-N`). That's expected for a fixture, but before public signup the real system needs unguessable, expiring tokens — out of scope for this code but on the checklist.

The body-`role` bypass is the blocker: it defeats invoice access control for every customer and should be fixed before signups open. Want me to apply the one-line fix and add the regression test?