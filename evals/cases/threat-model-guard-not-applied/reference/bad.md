# Security review

Last month's fixes hold. Export ignores the body's `customer_id`, quantities are bounded, signup
compares lowercased names, and the signing key comes from the environment.

Refunds are protected by staff_required through `STAFF_ONLY` and `permissions.protect`, and
`test_refund_staff_only` confirms it, so refunds correctly reject non-staff.

Remaining: passwords are stored in plain text, and there is no rate limit on login.
