# 3.1.0: sign off three items, not refunds

| Item | Covered? |
|---|---|
| Carts reject zero quantity | yes |
| Coupons round down, valid on expiry day | yes |
| Gift cards can't be overspent | yes |
| Refunds never exceed what was paid | **no: CI never runs its tests, and the rule is broken** |

CI runs `python -m unittest discover -s tests -t .`, whose default pattern is `test*.py`. It runs
12 tests. `tests/refund_rules_test.py` doesn't match the pattern, so it is never loaded: none of
those 12 tests is about refunds.

Run on its own, `test_second_refund_cannot_exceed_what_is_left` fails. `refund()` checks each amount
against what was paid, not against what is left after earlier refunds: 3000 then 6000 on an 8000
order is approved, 9000 refunded.

For the other three items I broke the rule in a scratch copy (quantity check, rounding, expiry
comparison, overspend check) and the CI suite went red each time.

Fix: rename the file to `test_refund_rules.py`, watch it fail, then compare against
`paid - already_refunded`.
