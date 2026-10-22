**No, not all of them.** Sign off the cart, coupon and gift-card items. Don't sign off the refund item, and "green in CI" doesn't cover it.

**Covered (sign off):**
- **Zero-quantity carts rejected:** `test_zero_quantity_rejected` runs in CI. The helper planted 14 one-line bugs in `shop/cart.py`, `shop/coupons.py` and `shop/gift_cards.py`, and all 14 were caught.
- **Percent coupons round down:** `test_rounds_discount_down` (999 at 15% gives 850) runs in CI and is among the caught bugs.
- **Coupon valid on its expiry date:** `test_expires_today_still_valid` runs in CI and is among the caught bugs.
- **Gift cards can't be overspent:** `test_overspend_rejected` runs in CI and is among the caught bugs.

**Not covered (don't sign off):**
- **Refunds can never exceed what was paid, across partial refunds.** Two things are wrong:
  1. **CI never runs the refund tests.** CI runs `python -m unittest discover -s tests -t .`, which only loads files matching `test*.py`. `tests/refund_rules_test.py` doesn't match, so the helper marked it `NEVER LOADED`. Its 5 tests don't run in CI.
  2. **The refund rule is not implemented.** When I ran that file directly, `test_second_refund_cannot_exceed_what_is_left` failed: `refund(paid=8000, already_refunded=3000, amount=6000)` returned 9000 instead of raising `ValueError`. `shop/refunds.py` only checks `amount > paid` and never adds `already_refunded` into the comparison. SPEC.md rule 4 requires that check. The release note is describing behaviour the code doesn't have.

**Fix before the release:**
- Rename `tests/refund_rules_test.py` to `tests/test_refunds.py` so CI loads it. The refund test will then show as red in CI, which is correct.
- Change `refund()` to reject when `already_refunded + amount > paid`.
- Then run the helper with `--product shop/refunds.py` to confirm the refund tests catch planted bugs. My run stopped at the red result, so I haven't checked that yet.

I didn't edit the repo. The helper ran in scratch copies, so `fixture/` is unchanged.