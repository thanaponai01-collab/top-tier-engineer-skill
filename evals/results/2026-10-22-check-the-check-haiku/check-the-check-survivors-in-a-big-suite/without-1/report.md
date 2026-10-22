The gate can't see a dropped volume discount on the billed path, so someone could ship a change that charges list price to 10+ seat accounts and all 29 tests would stay green.

**Why it survives:** every discount assertion goes through `seat_price()`. `monthly_amount`, `annual_amount`, and `invoice` are only tested with 1–3 seats, which are never discounted. Coverage is full because the discount branch runs, but no test checks that its result reaches the invoice.

I checked this by mutating a scratch copy of `billing.py` and running the suite (the fixture itself is unchanged):

| Mutation | Result |
|---|---|
| `monthly_amount` returns `PLANS[plan] * seats` (drops discount) | **passes** |
| `invoice` computes `PLANS[plan] * seats` (drops discount on the invoice path) | **passes** |
| Volume tier `20` changed to `21` (10% now starts at 21 seats) | **passes** |
| Annual charges 12 months instead of 10 | fails (caught) |
| Prorate floors instead of rounding half up | fails (caught) |
| Grace check `<=` changed to `<` | passes, but this is equivalent: at day 7 the formula already yields 0, so it isn't a bug |

Other gaps the gate doesn't pin:
- **Tier boundary at 20.** No test uses 19 or 20. `test_twenty_five` and `test_forty_nine` would still pass if the 10% tier started at 21.
- **Negative credit.** `apply_credit(5000, -300)` returns `(5300, -300)`, which inflates the amount due. SPEC.md doesn't cover negative credit, so this is an unspecified edge rather than a clear bug.
- **Zero-day period.** `prorate(100, 0, 0)` isn't tested. It presumably raises `ZeroDivisionError`, which is an unhandled crash rather than the documented `ValueError`.

To close the discount gap before outside changes land, I'd add these tests (values computed from the spec):
- `seat_price("team", 19) == 2755` and `seat_price("team", 20) == 2610`
- `monthly_amount("team", 10) == 27550`
- `annual_amount("team", 20) == 522000`
- `invoice("team", 25) == (23490, 0)`
- A negative-credit case, once you decide what it should do.

I can add these tests and rerun the mutants if you want.