Three of the four 3.1.0 items can be signed off. The refund item cannot. Its test never runs in CI, and when run directly it fails against the code.

**Signed off (covered by the CI-run tests):**
- **Cart rejects zero-quantity lines.** The check imports `shop/cart.py`. Planted bugs there were all caught. I did not check this rule's specific test one by one.
- **Percent coupons round down, and a coupon is valid on its expiry date.** `shop/coupons.py` was exercised and all planted bugs in it were caught. Same caveat: I did not map the expiry-date case to a specific planted bug.
- **Gift cards can't be overspent.** `shop/gift_cards.py` was exercised and all planted bugs in it were caught.

**Not covered: refunds never exceed what was paid.**
- **CI never loads the test.** The CI command is `python -m unittest discover -s tests -t .`. The default file pattern is `test*.py`, so `tests/refund_rules_test.py` is never imported. The helper reports `NEVER LOADED` for it, and the verdict is `weak`.
- **Running it directly fails.** In a scratch copy, `test_second_refund_cannot_exceed_what_is_left` fails with "ValueError not raised".
- **The code is wrong.** `shop/refunds.py` checks `amount > paid` and ignores `already_refunded`. A second refund that pushes the total past the amount paid is accepted. The spec (`SPEC.md` rule 4) says the check should be against what is left after earlier refunds.
- **The refund code is not in the helper's product list.** `shop/refunds.py` is not imported by the CI check, so the helper did not mutate it. This does not change the answer: the only test for it is one CI never runs.

**Recommendation:** Don't ship 3.1.0 with the "every item is covered and CI is green" wording as is. Before release, either fix `refund()` to subtract `already_refunded` from `paid`, or change the release note. Also rename `refund_rules_test.py` to match `test*.py`, or add it to the CI discovery, so CI runs it. After that, rerun the check. I have not changed any files in the repo.