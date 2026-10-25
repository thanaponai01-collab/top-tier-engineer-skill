One serious hole: **any customer can refund any invoice.** The staff-only guard is never applied to
the route. `permissions.protect(...)` swaps `app.r_refund` for the wrapped version, but the `ROUTES`
table was built earlier and still points at the original function. I ran it: bob's token on
`/refunds/100` got 200 and alice's credit went up by 42.50. The unit test passes only because it
calls the wrapped name instead of going through `handle`.

Everything else I attacked held: export ignores `customer_id`, invoice reads check the owner,
negative quantities and case-variant signups are refused. The catalog is public on purpose.
