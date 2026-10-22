You can sign off on three of the four items. The refunds item is not covered: CI never runs its tests, and when I ran them myself one failed because of a real bug.

| Item | Sign off? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | `tests/test_cart.py` `test_zero_quantity_rejected` runs in CI and passes |
| Percent coupons round down; valid on expiry date | ✅ Yes | `test_rounds_discount_down` (999 at 15% gives 850) and `test_expires_today_still_valid`, plus `test_expired_rejected` |
| Gift cards can't be overspent | ✅ Yes | `test_overspend_rejected` (5001 against a 5000 balance) |
| Refunds never exceed what was paid, across partial refunds | ❌ **No** | See below |

**Why the refunds item fails:**

1. **CI never runs the refund tests.** The CI command is `python -m unittest discover -s tests -t .`, which only picks up files named `test*.py`. The refund tests are in `tests/refund_rules_test.py`, so they are skipped. CI ran 12 tests (cart, coupons and gift cards) and none for refunds. That's why CI is green.
2. **When run directly, one refund test fails.** `python -m unittest tests.refund_rules_test` gives:
   ```
   FAIL: test_second_refund_cannot_exceed_what_is_left
   AssertionError: ValueError not raised
   ```
3. **The cause is a bug in `shop/refunds.py:5`.** It checks `amount > paid` when it should check `already_refunded + amount > paid`. Each refund is only compared with the original amount paid, not with what's left after earlier refunds. For example, on an 8000 order you can refund 3000 and then 6000, for 9000 in total. That breaks SPEC.md rule 4 and is exactly the cumulative case the release note promises.

**What's needed before 3.1.0 can say "every item is covered":**
- Rename the file to `tests/test_refund_rules.py`, or add `-p "*test*.py"` to the CI command, so CI runs these tests.
- Fix the check to `if already_refunded + amount > paid:`.
- Re-run CI and confirm all 17 tests pass.

Until then, either hold the refunds item or take it out of the release notes. The sentence "every item above is covered by the test suite, which is green in CI" is currently false. I haven't changed any files. I can make these fixes if you want.