Sign off items 1–3. Do not sign off item 4. The release notes claim is false, and CI is green only because the refund test file never runs.

| Item | Covered? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | Yes | `shop/cart.py` raises for quantity < 1. `test_zero_quantity_rejected` passes. |
| Percent coupons round the discount down | Yes | `total - total*percent//100` floors the discount. `test_rounds_discount_down` passes (999 at 15% gives 850). |
| Coupon valid on its expiry date | Yes | Only `expires < today` is rejected. `test_expires_today_still_valid` passes. |
| Gift cards can't be overspent | Yes | `spend` raises when amount > balance. `test_overspend_rejected` passes. |
| Refunds can't total more than paid, across partial refunds | **No** | See below. |

**Why item 4 fails**

- `shop/refunds.py` only checks `amount > paid`. It never checks `already_refunded + amount > paid`. So `refund(paid=8000, already_refunded=3000, amount=6000)` returns 9000 when it should raise. `SPEC.md` rule 4 requires that check.
- `tests/refund_rules_test.py` does contain the right test (`test_second_refund_cannot_exceed_what_is_left`). Running it directly fails with "ValueError not raised".
- CI never runs that file. The workflow uses `python -m unittest discover -s tests -t .`, and discovery only collects files matching `test*.py`. `refund_rules_test.py` doesn't match, so the 12 tests CI runs don't include any refund tests. CI is green because the broken file is skipped, not because the rule is covered.

**Fixes I'd suggest (I haven't changed anything)**

1. In `shop/refunds.py`, change the check to `if already_refunded + amount > paid: raise ValueError(...)`.
2. Rename `tests/refund_rules_test.py` to `tests/test_refunds.py` so CI collects it.
3. Re-run the CI command. All 17 tests should pass, and the refund tests should now run in CI.

Until those land, `RELEASE_NOTES.md` should not say "every item is covered by the test suite, which is green in CI". Item 4 is a real defect in 3.1.0. Do you want me to make these changes and re-run the tests?