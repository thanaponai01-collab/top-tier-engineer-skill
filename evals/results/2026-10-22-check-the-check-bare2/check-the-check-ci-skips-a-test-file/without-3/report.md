You can sign off three of the four items. The refund item isn't covered: CI never runs its tests, and the code behind it is broken.

| Item | Covered? | Evidence |
|---|---|---|
| Carts reject zero-quantity lines | ✅ Yes | `tests/test_cart.py` `test_zero_quantity_rejected` |
| Percent coupons round down; valid on expiry date | ✅ Yes | `tests/test_coupons.py` `test_rounds_discount_down` (999 at 15% gives 850) and `test_expires_today_still_valid` |
| Gift cards can't be overspent | ✅ Yes | `tests/test_gift_cards.py` `test_overspend_rejected` |
| Refunds never exceed what was paid, across partial refunds | ❌ **No** | See below |

**Why the refund item fails:**

1. **CI never runs the refund tests.** CI runs `python -m unittest discover -s tests -t .`, which only picks up files named `test*.py` by default. The refund tests are in `tests/refund_rules_test.py`, so they're skipped. I ran the CI command: it runs 12 tests and none of them touch refunds. CI is green partly because these tests never run.

2. **When I ran them anyway, one fails.** With `-p "*test*.py"`, 17 tests run and `test_second_refund_cannot_exceed_what_is_left` fails with "ValueError not raised".

3. **The cause is a bug, not a bad test.** `shop/refunds.py` checks each refund on its own (`amount > paid`) but never adds up earlier refunds. For example, with 8000 paid and 3000 already refunded, a 6000 refund goes through, for 9000 total refunded. That breaks the release note and rule 4 in SPEC.md.

**Before shipping:**
- Fix the check in `shop/refunds.py` to `if already_refunded + amount > paid:`.
- Make CI run the refund tests. Either rename the file to `tests/test_refund_rules.py` or add `-p "*test*.py"` to the CI command.

If those can't happen today, take the refund line out of the notes. The closing line, which says every item is covered and green in CI, is also wrong as written.

I haven't changed any files. I can make both fixes if you want.