You can sign off on three of the four items. The refunds item is not covered, and the refund code itself has a bug.

| Item | Sign off? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | `tests/test_cart.py` → `test_zero_quantity_rejected`; `shop/cart.py` rejects `quantity < 1` |
| Percent coupons round down; still valid on the expiry date | ✅ Yes | `tests/test_coupons.py` → `test_rounds_discount_down` (999 − 15% → 850) and `test_expires_today_still_valid` |
| Gift cards can't be overspent | ✅ Yes | `tests/test_gift_cards.py` → `test_overspend_rejected` (5000 balance, spend 5001) |
| Refunds never exceed what was paid, across partial refunds | ❌ **No** | See below |

**Why the refunds item fails:**

1. **CI never runs the refund tests.** CI runs `python -m unittest discover -s tests -t .`, which only picks up files named `test*.py`. The refund tests are in `tests/refund_rules_test.py`, so they're skipped. I ran the exact CI command and it ran 12 tests: cart 5, coupons 4, gift cards 3, refunds 0. CI is green partly because these tests aren't in it.

2. **When the refund tests do run, one fails.** With `-p "*test*.py"`, 17 tests run and `test_second_refund_cannot_exceed_what_is_left` fails with "ValueError not raised".

3. **The bug is real.** `shop/refunds.py` checks `amount > paid` but ignores `already_refunded`. On an 8000 order with 3000 already refunded, a 6000 refund is approved and the total refunded becomes 9000. That breaks rule 4 in SPEC.md and is exactly the case the release note claims is covered.

**Before shipping 3.1.0:**
- Fix the check in `shop/refunds.py` to `if already_refunded + amount > paid:`.
- Make CI find the refund tests: rename the file to `tests/test_refund_rules.py`, or add `-p "*test*.py"` to the CI command.
- Correct the line in RELEASE_NOTES.md saying every item is covered until both are done.

I haven't changed any files. I can make these fixes if you want.