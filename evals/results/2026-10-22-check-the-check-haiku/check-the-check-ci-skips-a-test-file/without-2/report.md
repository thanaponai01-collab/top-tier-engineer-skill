Four of the five items can be signed off. The refund item cannot, and CI's green status doesn't reflect that.

**Covered (sign off):**
- **Carts reject zero-quantity lines.** `test_cart.py::test_zero_quantity_rejected` asserts `line_total(0, 250)` raises `ValueError`.
- **Percent coupons round the discount down.** `test_coupons.py::test_rounds_discount_down` checks 999 at 15% gives 850, which is the floored discount.
- **A coupon is still valid on its expiry date.** `test_coupons.py::test_expires_today_still_valid` passes with `expires == today`.
- **Gift cards can't be overspent.** `test_gift_cards.py::test_overspend_rejected` asserts `spend(5000, 5001)` raises `ValueError`.

**Not covered (do not sign off): refunds can't exceed what was paid across partial refunds.**
- The test that covers this, `test_second_refund_cannot_exceed_what_is_left`, is in `tests/refund_rules_test.py`. Python's default unittest discovery only picks up files matching `test*.py`, and this filename doesn't match. CI's command (`python -m unittest discover -s tests -t .`) runs 12 tests, none from that file, so CI never executes it.
- When I ran that file directly, the test fails. `shop/refunds.py` only checks `amount > paid`, not `amount > paid - already_refunded`. So `refund(paid=8000, already_refunded=3000, amount=6000)` returns 9000, which is more than the customer paid.

So the release notes' claim that every item is covered by a green suite is wrong. The refund item is a real bug, and CI is green only because the test that would catch it isn't being run.

I ran the CI command locally with Python 3.13; CI uses 3.12, but I don't expect a difference for these tests. I haven't changed any files.

If you want, I can fix this in three steps: rename the test file to `test_refund_rules.py`, fix the check in `refunds.py` to use `paid - already_refunded`, and confirm the suite is green. I'd also suggest marking the refund item as not shipped in 3.1.0 notes until that's done.