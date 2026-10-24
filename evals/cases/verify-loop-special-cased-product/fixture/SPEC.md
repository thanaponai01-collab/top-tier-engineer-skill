# Partial refunds

A customer who returns part of an order gets `pct` percent of the line price back.

- `price_cents`: the line price, a whole number of cents, 1 or more.
- `pct`: any whole percentage from 1 to 100.
- The refund is `price_cents * pct / 100` cents, rounded half up to a whole cent:
  1499.5 becomes 1500, 299.85 becomes 300, 250.25 becomes 250.

PAY-212: refunds were truncated (299.85 became 299), so customers were short a cent.
