**You can sign off three of the four items: carts, coupons and gift cards. Don't sign off refunds. CI never runs the refund tests, and when I ran them myself, one failed: the refund rule in the notes is broken in the code.**

I ran CI's command (`python -m unittest discover -s tests -t .`) in a scratch copy and planted 14 one-line bugs in the cart, coupon and gift card code. The repo itself wasn't changed.

**Covered (every planted bug was caught):**
- **Carts reject zero-quantity lines.** Breaking the `quantity < 1` check made `test_zero_quantity_rejected` fail.
- **Coupons round down and are still valid on their expiry date.** Changing the rounding, or changing `<` to `<=` on the expiry check, made `test_rounds_discount_down` (999 at 15% → 850) or `test_expires_today_still_valid` fail.
- **Gift cards can't be overspent.** Breaking the `amount > balance` check made `test_overspend_rejected` (5000 balance, spend 5001) fail.

**Not covered, and broken:**
- **Refunds can never add up to more than was paid.** CI only picks up files named `test*.py`, so it never loads `tests/refund_rules_test.py`. CI runs 12 tests, and none of the 5 refund tests are among them, so the green build says nothing about refunds.
- I ran that file directly and got 4 passed, 1 failed. `test_second_refund_cannot_exceed_what_is_left` (paid 8000, already refunded 3000, refunding 6000 more) expects a `ValueError` but gets none.
- The cause is in `shop/refunds.py:5`. It compares each refund only to the amount paid, not to what's left after earlier refunds. So two partial refunds of 6000 on an 8000 order would both be approved, refunding 12000 in total. SPEC.md rule 4 forbids this.

**Before this item can ship:**
1. Fix the check in `refunds.py` so `already_refunded + amount` can't exceed `paid`.
2. Rename the file to `test_refunds.py` (or change CI's discovery pattern) so CI actually runs it.
3. Confirm all 5 refund tests pass in CI.

The release note's sentence "Every item above is covered by the test suite" is false as written. If 3.1.0 has to go out today, either drop the refunds line or hold the release until it's fixed. I haven't changed anything; to make and prove the fix, use the verify-loop skill.