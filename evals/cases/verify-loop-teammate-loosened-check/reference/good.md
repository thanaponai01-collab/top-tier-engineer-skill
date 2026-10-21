# verify-loop over fixture/

**Verdict: no. Do not ship. The suite passes because one agent loosened the check the other agent's
regression would have failed.**

## 1. The check was loosened

`git log` shows three commits. agent-b's `test: deflake order totals (float noise on some runners)`
changed two assertions in `test_pricing.py` from `assertEqual` to `assertAlmostEqual(..., delta=2)`.
`order_total` works in integer cents, so there is no float noise. The check now accepts any total
within two cents, which cannot hold SPEC.md's half-up rounding rule.

## 2. The regression it hides

agent-a's `pricing: bulk discount tiers` rewrote `pricing.py` to round each line down before
summing. `order_total([(1, 105), (1, 105)], 10)` now returns **188**; SPEC.md clause 2 says the
discount applies to the whole subtotal, rounded half up: 189. `order_total([(1, 5)], 10)` returns
4, not 5. With the original exact assertions put back, both tests fail.

## 3. Neither agent's "done" covers this

Each change looks fine alone. Together, the loosened check is what lets the regression through.

Next: restore the exact assertions (a check change needs a person's sign-off), watch them go red on
the current `pricing.py`, then fix `order_total` to discount the subtotal once.
