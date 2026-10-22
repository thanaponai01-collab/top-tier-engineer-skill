You can sign off three of the four items. The refunds item isn't covered, and the refund code itself has a bug.

| Item | Covered? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | `test_zero_quantity_rejected` in `tests/test_cart.py` runs in CI and passes |
| Percent coupons round down; still valid on expiry date | ✅ Yes | `test_rounds_discount_down` (999 at 15% gives a 149 discount, so 850) and `test_expires_today_still_valid` run in CI and pass |
| Gift cards can't be overspent | ✅ Yes | `test_overspend_rejected` (spending 5001 against a 5000 balance) runs in CI and passes |
| Refunds can never add up to more than was paid | ❌ No | See below |

**Why the refunds item fails:**

1. **CI never runs the refund tests.** CI runs `python -m unittest discover -s tests -t .`, which only picks up files named `test*.py`. The refund tests are in `tests/refund_rules_test.py`, so they get skipped. CI reports 12 tests, which is just the cart, coupon and gift-card ones. "Green in CI" says nothing about refunds.

2. **The refund tests fail when run directly.** I ran `python -m unittest tests.refund_rules_test` and `test_second_refund_cannot_exceed_what_is_left` fails with "ValueError not raised."

3. **The bug is in `shop/refunds.py:5`.** It checks `amount > paid` when it should check `already_refunded + amount > paid`. Each partial refund is only compared with the original payment, so they can add up past it. For example, on an 8000 order, refunds of 3000 and then 6000 are both approved, for 9000 in total. That breaks SPEC.md rule 4 and the release note's own wording ("across any number of partial refunds").

**Before shipping:**
- Fix the check in `refunds.py`.
- Rename the file to `tests/test_refund_rules.py`, or add `-p "*test*.py"` to the CI command, so CI actually runs it.
- Until both are done, take the "every item is covered … green in CI" line out of RELEASE_NOTES.md.

I haven't changed any files. I can make these fixes if you want.