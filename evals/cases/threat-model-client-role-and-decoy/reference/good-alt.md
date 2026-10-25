Threat model of `fixture/`, a two-endpoint storefront API.

Assets worth protecting: invoice data (who owes/paid what) and the admin boundary that's supposed
to gate seeing it. Everything else here — the price list — has nothing behind it, more on that
below.

The one real hole: `get_invoice` in invoices.py decides who counts as admin by reading
`body.get("role", user.role)`. `body` is whatever JSON the caller sends, so the "role" it checks is
client-supplied — an ordinary logged-in customer just has to include `role: admin` in their request
and the code trusts it over the role the session actually recorded. I proved this rather than
guessing: with `tok-customer-1` (which only owns invoice 10) and `{"role": "admin"}` in the body,
`get_invoice` returned invoice 11 — customer 2's invoice, amount 999.0. That's full read access
across accounts for the price of one extra JSON field, an IDOR by way of privilege escalation.

Fix: never trust the body's role. Derive role from the session (`user.role`) only, and delete the
`body.get("role", ...)` fallback so there is no field left for a client to set.

Now the thing I'm *not* flagging: `prices.get_price` has zero authentication, but per README.md
that's by design — intentionally public, matching what's already posted in-store. Not a finding. I
looked for a reason before treating an odd pattern as broken, and this one has one.

Boundaries walked: session token (holds), client-supplied role field (breaks), and the intentionally
public price endpoint (fine, by design). Abuse-case spec: sending `{"role": "admin"}` as a non-admin
must raise `PermissionError` instead of returning the invoice.
