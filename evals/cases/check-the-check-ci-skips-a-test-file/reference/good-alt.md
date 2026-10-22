You can sign off the cart, coupon and gift-card items: their tests are in CI and fail when I break
those rules.

Not refunds. The refund tests live in tests/refund_rules_test.py, and unittest discover only picks
up test*.py, so CI never runs them (12 tests, all cart/coupons/gift cards). When I run that file
directly, one test fails: refund() compares each refund with the amount paid and ignores
already_refunded, so two partial refunds can add up to more than the customer paid.
