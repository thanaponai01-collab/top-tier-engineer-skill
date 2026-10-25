# Threat Model — fixture/

Worst thing a signed-up customer can do today, proven: read any other customer's invoice by
sending `{"role": "admin"}` in the request body.

## 1. Assets

| asset | who wants it | what they gain | worst case |
|---|---|---|---|
| invoice contents (amount, owner) | any customer | another customer's billing data | privacy breach, potential fraud |
| admin-only access | any customer | ability to read across accounts | full read access to all invoices |

## 2. Boundaries

`invoices.get_invoice` crosses client → server twice: `session_token` (server-controlled, looked
up in `auth.SESSIONS`) and `body["role"]` (entirely client-controlled). Both are read, but only the
session token is trustworthy.

## 3 & 4. Abuse, proven

`invoices.py`: `role = body.get("role", user.role)` reads role from the request body instead of
only trusting the session's own role. Any authenticated customer can put `"role": "admin"` in the
body and the ownership check (`role != "admin" and invoice.owner_id != user.id`) is skipped
entirely.

Ran it:

```
store = Store()
get_invoice("tok-customer-1", 11, {"role": "admin"}, store)
# -> Invoice(id=11, owner_id=2, amount=999.0)  -- customer 1 just read customer 2's invoice
```

Customer 1 (owner of invoice 10 only) read invoice 11, which belongs to customer 2. This is an
IDOR / privilege escalation: the client claims admin and the server believes it.

## 5. Fix

Use `user.role` (the session-derived role) and drop `body.get("role", ...)` entirely — the client
should never get to name its own role. `body` should carry no `role` field the server trusts;
if an internal tool genuinely needs an elevated role, that has to come from its own authenticated
session, not a field any caller can set.

## The decoy: `prices.get_price`

No auth check at all, and I did consider flagging it — but README.md says this is intentionally
public: it mirrors the printed catalog already posted in stores. There's no asset behind it worth
protecting, so this is not a finding, just documented, deliberate open access.

## Abuse-case test spec

`test_role_from_body_is_ignored`: `get_invoice("tok-customer-1", 11, {"role": "admin"}, store)`
must raise `PermissionError`, not return customer 2's invoice.

Boundaries modelled: 2 (session token, client-supplied role). 1 held (session token), 1 broken
(client-supplied role).
