You can sign off three of the four items. The refunds item is not covered, and the refund code is actually broken.

| Release note item | Sign off? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | I planted one-line bugs in `shop/cart.py` and the suite failed every time. |
| Percent coupons round down; a coupon is still valid on its expiry date | ✅ Yes | Same for `shop/coupons.py`. Breaking the `expires < today` check or the round-down made the suite fail. |
| Gift cards can't be overspent | ✅ Yes | Same for `shop/gift_cards.py`. Changing the `amount > balance` check made the suite fail. |
| Refunds never add up to more than was paid, across partial refunds | ❌ **No, and it's a real bug** | Details below. |

Across the three covered items I planted 14 one-line bugs, and CI's command (`python -m unittest discover -s tests -t .`, 12 tests) failed on all 14.

**What's wrong with refunds:**

- **CI never runs the refund tests.** `tests/refund_rules_test.py` doesn't match unittest's default `test*.py` file pattern, so its 5 tests are silently skipped. The green CI says nothing about refunds.
- **When I ran that file directly, it fails.** In a temp copy, `test_second_refund_cannot_exceed_what_is_left` fails with `ValueError not raised`. Running the whole suite including that file gives 17 tests and 1 failure.
- **The bug is in the product code, not the test.** `shop/refunds.py` checks `amount > paid` but not `already_refunded + amount > paid`. So on an order paid at $80.00, after a $30.00 refund, a further $60.00 refund is approved, bringing the refunded total to $90.00. SPEC.md rule 4 says it must be rejected because only $50.00 is left. Every partial refund passes as long as each one is no larger than the original payment, so repeated refunds can drain any amount.

**Before you ship:**
1. Change the refund check so the new total (`already_refunded + amount`) can't exceed `paid`.
2. Make CI run the refund tests. Either rename the file to `tests/test_refund_rules.py` or add `-p "*test*.py"` to the command in `ci.yml`. Right now it can't catch this, even with the test already written.
3. Remove the "every item is covered" line from RELEASE_NOTES.md until both are done, or hold the refunds item.

I didn't change anything in the repo; all runs were in temp copies. If you want me to make the fix and prove it (seen failing, then passing), I can do that with the verify-loop skill.