You can sign off three of the four items. The refunds item isn't covered: its tests never run in CI, and when I ran them myself, one fails.

| Release note item | Covered? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | `tests/test_cart.py` → `test_zero_quantity_rejected` passes |
| Percent coupons round the discount down; still valid on the expiry date | ✅ Yes | `tests/test_coupons.py` → `test_rounds_discount_down` (999 at 15% → 850, so the discount 149.85 rounds down to 149) and `test_expires_today_still_valid` pass |
| Gift cards can't be overspent | ✅ Yes | `tests/test_gift_cards.py` → `test_overspend_rejected` passes |
| Refunds can never total more than was paid | ❌ **No** | See below |

**Why the refunds item fails:**

1. **CI never runs its tests.** CI runs `python -m unittest discover -s tests -t .`, which only picks up files named `test*.py` by default. The refund tests are in `tests/refund_rules_test.py`, so they're skipped. CI is green because it ran 12 tests from the other three files and none for refunds.
2. **The code has a bug, and the test that would catch it fails.** When I ran every test file (`-p "*test*.py"`), 17 tests ran and one failed:
   ```
   FAIL: test_second_refund_cannot_exceed_what_is_left
   AssertionError: ValueError not raised
   ```
   `shop/refunds.py:5` compares each refund to the full amount paid (`amount > paid`), not to what's left after earlier refunds. So on an 8000 order with 3000 already refunded, a 6000 refund goes through and the total refunded reaches 9000. That breaks rule 4 in SPEC.md and is the exact case the release note promises can't happen.

**Before shipping:**
- Fix the check to `if already_refunded + amount > paid:`.
- Make sure CI runs the refund tests: rename the file to `tests/test_refund_rules.py`, or add `-p "*test*.py"` to the CI command.
- Or drop the refunds line from the 3.1.0 notes, and the "every item is covered" sentence, until both are done.

I didn't change any files.