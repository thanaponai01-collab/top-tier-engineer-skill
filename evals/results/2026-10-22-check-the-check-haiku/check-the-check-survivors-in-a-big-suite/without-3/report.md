The gate misses a bug where a split payment silently drops cents. I checked that and three other gaps by mutating a scratch copy of `billing.py` and running the existing suite. Each of these mutants passes all 29 tests:

1. **Split payments lose the remainder.** `split_payment` could return `[base] * ways`, which drops `total % ways` cents on every split. Every split test uses an amount that divides evenly (9000/3, 12000/4, 4321/1), so the "parts add up" test never sees a remainder. Spec rule 6 says the parts always sum to the total, and nothing enforces it. Money vanishes without an error. This is the most serious gap.

2. **The 20-seat discount tier.** Changing `(20, 10)` to `(21, 10)` passes. The tests check 9, 10, 25, 49, and 50 seats, but not 19 or 20. Spec rule 2 says 20 or more seats get 10% off, so 20 seats would be billed at list price minus 5%.

3. **Annual billing with a volume discount.** Replacing `monthly_amount(...) * 10` with `PLANS[plan] * seats * 10` passes. The annual tests use 2 and 3 seats, both below the first discount tier, so annual pricing for 10+ seats is never checked. The mutant overcharges any annual account with a discount.

4. **Remainder allocation order.** Giving the extra cents to the last parts instead of the first (spec rule 6 says the first parts carry them) passes. The sum test cannot tell the two apart, and no test has a nonzero remainder with more than one part.

Two smaller things the tests also don't cover:
- `prorate(100, 0, 0)` raises `ZeroDivisionError` instead of a `ValueError`. It's a crash, not a wrong amount.
- `split_payment(2, 5)` returns `[1, 1, 0, 0, 0]`. The spec doesn't say what should happen here, so I'd settle that with the product owner before writing a test.

"Every statement runs" is true, but it's a weak claim here. The tests exercise each line without checking the boundary values or the cases where the arithmetic has a remainder.

Before the outside team touches billing, I'd add tests for: a split with a nonzero remainder (checking the sum and that the first parts get the extra cents), 19/20 seats, and annual pricing at 10+ seats. I can write those now and confirm the four mutants fail. I haven't changed anything in `fixture/`.