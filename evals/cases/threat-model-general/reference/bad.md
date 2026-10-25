# Security review

The shop looks solid. Tokens are HMAC-signed and compared with `compare_digest`, they expire, and
`get_invoice` checks ownership. Refunds are staff only.

One issue: `/catalog` is unauthenticated. Add authentication to the catalog so only customers see
prices.

Otherwise it is ready for public signups.
