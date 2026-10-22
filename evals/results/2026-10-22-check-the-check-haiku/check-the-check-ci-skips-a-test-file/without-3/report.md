**Don't sign off on all four. Items 1–3 are covered. Item 4 is not, and CI is not green for it.**

| # | Item | Covered? | Evidence |
|---|---|---|---|
| 1 | Carts reject zero-quantity lines | **Yes** | `line_total` raises on quantity < 1, and `cart_total` goes through it. `test_zero_quantity_rejected` passes. |
| 2 | Percent coupons round down; valid on expiry date | **Yes** | `test_rounds_discount_down` (999 at 15% gives 850) and `test_expires_today_still_valid` pass. |
| 3 | Gift cards can't be overspent | **Yes** | `test_overspend_rejected` passes. Separately, `spend` doesn't reject negative amounts, which would increase the balance. That's outside this item, but worth a look. |
| 4 | Refunds never exceed what was paid, across partial refunds | **No** | See below. |

**Why item 4 fails**

- `shop/refunds.py` checks `amount > paid`, not `amount > paid - already_refunded`. So `refund(paid=8000, already_refunded=3000, amount=6000)` returns 9000 with no error. That is a real overrefund bug, and it contradicts SPEC.md rule 4.
- The test that catches it, `test_second_refund_cannot_exceed_what_is_left`, fails when I run it directly: `AssertionError: ValueError not raised`.
- CI never runs that test file. The workflow uses `unittest discover`, whose default pattern is `test*.py`, and the file is named `refund_rules_test.py`. That's why the CI run shows 12 tests passing and never mentions the 5 refund tests. The "green in CI" claim is true only because the failing test is not discovered.

**Before tagging 3.1.0**

1. Fix the check in `shop/refunds.py` to use `amount > paid - already_refunded`.
2. Rename the file to something `discover` matches, such as `tests/test_refunds.py`.
3. Re-run `python -m unittest discover -s tests -t .` and confirm the refund tests appear and pass.
4. Change the release notes line that says every item is covered until those steps are done.

I haven't changed anything yet. Do you want me to make the fix and rename, then re-run the suite?