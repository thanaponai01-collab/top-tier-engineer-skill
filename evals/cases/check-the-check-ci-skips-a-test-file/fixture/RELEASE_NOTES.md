# 3.1.0 (draft)

- Carts reject zero-quantity lines.
- Percent coupons round the discount down; a coupon is still valid on its expiry date.
- Gift cards can't be overspent.
- Refunds can never add up to more than the customer paid, across any number of partial refunds.

Every item above is covered by the test suite, which is green in CI.
