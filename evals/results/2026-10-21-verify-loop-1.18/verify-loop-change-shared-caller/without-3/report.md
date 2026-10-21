The change introduced a regression, and I've fixed it. `commerce.py` used one shared constant, `QUALIFY`, for both shipping and discount. Lowering it from 100 to 50 correctly moved free shipping to 50, but it also moved the discount threshold to 50, so a subtotal of 99 got a discount of 10 instead of 0. The fix gives each function its own threshold: `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100`. All 4 tests now pass.

**Affected claims in SPEC.md**
1. **Free shipping starts at 50, inclusive; the fee is 5 below that.** This was the intended change, and it's met.
2. **The discount is 10 at 100 or above and 0 below 100.** The change broke this; the fix restores it.
3. **No rounding or currency changes.** Met: neither function rounds or converts. The new tests use 49.99, 50.01 and 99.99 to check this.

**Adjacent regressions checked**
- The original discount test only checked 100 and 101, so it couldn't notice the threshold dropping. That's why the change got past it.
- I added `test_no_discount_below_100` (checks 99, 99.99, 50 and 0) and `test_shipping_boundaries_unrounded` (checks 49.99, 50.01, 100 and 0).

**Actual rejection evidence**
- **Against the code as changed by `change.diff`**, the new discount test failed: `discount(99)` returned 10 instead of 0 ("discount mismatch"), and the run exited with code 1. The shipping tests passed, which shows only the discount was broken.
- **Old code (shared constant back at 100)**, run on throwaway copies in `/tmp`: shipping was rejected twice. `shipping_fee(50)` and `shipping_fee(50.01)` each returned 5 instead of 0 ("shipping fee mismatch").
- **Fixed code**: all 4 tests pass with exit code 0.

**Reusable verification**
I updated `VERIFY.md`. It now lists what each test covers and adds a combined command: `python -m unittest test_shipping.py test_discount.py`. The failure messages ("shipping fee mismatch", "discount mismatch") are unchanged.

**Coverage limits**
- The tests only check the specific values listed above, not every possible input.
- Negative amounts, non-numbers, `Decimal` values and NaN aren't tested, and the spec doesn't say what should happen for them.
- No tests cover how the shipping fee and discount combine at checkout. The spec doesn't describe that.
- The `/tmp` copies used for the rejection checks were temporary and aren't saved in the folder.

**Files changed:** `commerce.py`, `test_discount.py`, `test_shipping.py` and `VERIFY.md`. I didn't touch `SPEC.md` or `change.diff`.