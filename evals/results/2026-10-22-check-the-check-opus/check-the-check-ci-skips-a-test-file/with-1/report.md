You can sign off three of the four items: carts, coupons and gift cards. Don't sign off refunds. CI never runs the refund tests, and when run directly one of them fails because there is a real bug in the code.

**What CI actually runs.** `python -m unittest discover -s tests -t .` picks up only files named `test*.py`. It ran 12 tests in `test_cart.py`, `test_coupons.py` and `test_gift_cards.py`. `tests/refund_rules_test.py` doesn't match that pattern, so its 5 tests have never run in CI. The green build says nothing about refunds.

**Covered (I planted 14 one-line bugs across cart, coupons and gift cards; the suite caught all 14, none survived):**
- **Carts reject zero-quantity lines:** covered. Breaking the `quantity < 1` check turned the suite red.
- **Percent coupons round down, and a coupon is still valid on its expiry date:** covered. `999 at 15% → 850` checks the rounding and `expires == today → valid` checks the date edge; both failed when I broke the code.
- **Gift cards can't be overspent:** covered. `spend(5000, 5001)` fails when the `amount > balance` check is broken.

**Not covered: "Refunds can never add up to more than the customer paid, across any number of partial refunds."**
- No CI test touches refunds, for the reason above.
- I ran `refund_rules_test.py` directly in a temp copy: 4 passed, 1 failed. `test_second_refund_cannot_exceed_what_is_left` fails with "ValueError not raised".
- The bug is in `shop/refunds.py:6`. It compares each refund to the full amount paid (`amount > paid`) rather than to what is left after earlier refunds, which SPEC.md rule 4 requires. So on an $80.00 order with $30.00 already refunded, a $60.00 refund is approved and the total refunded reaches $90.00. That is exactly what this release-note item says can't happen.

If 3.1.0 ships today, either pull the refund line from the release notes or hold until two things are fixed:
1. The refund check in `refunds.py` should compare against `paid - already_refunded`. Done right, the existing test (8000 paid, 3000 refunded, 6000 requested → ValueError) passes.
2. The test file needs a name CI collects, such as `test_refunds.py`, or the CI discover command needs `-p "*_test.py"`. Without that, CI stays green even with the bug.

I haven't changed anything in `fixture/`. If you want the fix made and proven (failing first, then passing), the verify-loop skill can do that.