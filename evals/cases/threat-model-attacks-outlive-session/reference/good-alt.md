`gizmo-pro` is in the catalog. One test fails, and it is a security one: a customer who sends a
`customer_id` to the export route gets someone else's invoices. Export changed since the last
review and now trusts that field for everyone, not just staff. Hold the deploy until it is fixed.
