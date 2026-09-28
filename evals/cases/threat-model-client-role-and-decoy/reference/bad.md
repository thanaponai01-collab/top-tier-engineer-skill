# Threat Model — fixture/

Checked both endpoints.

`invoices.get_invoice` looks fine: it requires a valid session token, and the ownership check
(`invoice.owner_id != user.id`) means a normal customer can't reach someone else's invoice. The
`body.get("role", ...)` fallback is there for internal admin tools that pass their role alongside
the request, per the code comment — that's an established internal pattern, not user input in the
usual sense.

`prices.get_price` has no authentication check whatsoever — anyone can call it with no session.
This should require a login like the invoices endpoint does.

Recommendation: add authentication to `get_price`.
