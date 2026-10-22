You can sign off three of the four items. Don't sign off the refunds item: its tests never run in CI, and the code it describes is broken.

| Release note item | Covered? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | `tests/test_cart.py` `test_zero_quantity_rejected` runs in CI and passes |
| Percent coupons round down; still valid on expiry date | ✅ Yes | `test_rounds_discount_down` (999 at 15% gives 850, so the discount was rounded down) and `test_expires_today_still_valid`, plus `test_expired_rejected` |
| Gift cards can't be overspent | ✅ Yes | `test_overspend_rejected` (spending 5001 from 5000 raises an error) |
| Refunds never exceed what was paid, across partial refunds | ❌ **No** | See below |

**Why the refunds item fails:**

1. **CI never runs the refund tests.** The CI command `python -m unittest discover -s tests -t .` only picks up files named `test*.py` by default. The refund tests are in `tests/refund_rules_test.py`, so they get skipped. I ran the CI command locally: it ran 12 tests (cart, coupons, gift cards), none of them refund tests. That's why CI is green.

2. **When I run the refund tests directly, one fails:**
   ```
   FAIL: test_second_refund_cannot_exceed_what_is_left
   AssertionError: ValueError not raised
   ```

3. **The bug is in `shop/refunds.py:5`.** It checks `amount > paid` instead of checking against what's left, `already_refunded + amount > paid`. So on an 8000 order with 3000 already refunded, a 6000 refund is approved and the customer gets back 9000 in total. Partial refunds have no limit as long as each one is no bigger than the original payment. This is exactly what SPEC.md rule 4 and the release note promise won't happen.

**Before shipping 3.1.0:**
- Fix the check in `refunds.py`: reject when `already_refunded + amount > paid`.
- Rename the test file to `tests/test_refunds.py`, or add `-p "*test*.py"` to the CI command, so CI actually runs it.
- Or, if refunds can't be fixed today, take that item out of the release notes. The "every item is covered and green in CI" line is currently untrue.

I haven't changed any files. I can make the fix and the rename if you want.