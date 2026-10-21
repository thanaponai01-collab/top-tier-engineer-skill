The change broke the discount. Lowering the shared `QUALIFY` constant from 100 to 50 lowered the free-shipping threshold as intended, but it also made `discount()` give 10 off orders between 50 and 99.99. The spec says no discount below 100. I fixed it, and all 4 tests now pass.

**Affected claims (SPEC.md)**
1. Free shipping at a subtotal of 50 or more, fee of 5 below that. This is what the change intended, and it works.
2. Discount of 10 at 100 or more, 0 below 100. **This one regressed.** `discount(99.99)` returned 10.
3. Both functions use the amount as given, with no rounding.

**The regression and the evidence**
- The old tests passed on the broken code. `test_discount.py` only checked 100 and 101, so it never saw the lowered threshold.
- I added `test_no_discount_below_100`, which checks 99.99, 99, 50 and 0. Run against the changed code, it fails: `AssertionError: 10 != 0 : discount mismatch` at `discount(99.99)`.
- **Fix in `commerce.py`:** I split `QUALIFY` into `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100`, so each function has its own threshold.

**Nearby checks**
- I added `test_shipping_boundaries_unrounded`, which checks 49.99, 50.01, 100 and 0.
- I made deliberately broken copies of the shipping code to confirm the tests catch them, and they do:
  - Shipping threshold put back to 100: fails with `5 != 0 : shipping fee mismatch`.
  - `round(total)` added to shipping: fails with `0 != 5 : shipping fee mismatch`, because 49.99 rounds up to 50.
- After each experiment I restored the fixed file, and the full run passes.

**Reusable verification**
`VERIFY.md` now lists the spec claim next to each test command and failure message. It also has a combined command: `python -m unittest test_shipping.py test_discount.py`.

**Coverage limits**
- I didn't run the rounding experiment against `discount()`. It probably wouldn't be caught there anyway, since no discount test uses an amount near 100 that rounds across it, like 99.5.
- "No currency changes" is only checked indirectly, through the exact amounts returned.
- Negative, `None` and non-numeric inputs aren't tested; the spec doesn't define them.
- I only edited `commerce.py`, the two test files and `VERIFY.md`. `SPEC.md` and `change.diff` are unchanged.