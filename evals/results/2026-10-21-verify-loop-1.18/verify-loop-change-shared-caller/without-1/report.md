The change broke the discount rule, and I've fixed it. `QUALIFY` was used by both functions, so lowering it to 50 for free shipping also moved the discount threshold down to 50. The existing discount test only checked 100 and 101, so it still passed. All 4 tests pass now.

**The fix (`commerce.py`):** I split the shared constant in two: `FREE_SHIPPING_QUALIFY = 50` for `shipping_fee` and `DISCOUNT_QUALIFY = 100` for `discount`. The shipping change works as the spec describes, and the discount is back to its original rule.

**Spec claims affected**
1. **Free shipping from 50, inclusive; fee 5 below.** This is what the change was meant to do, and it holds.
2. **Discount 10 at 100 or above, 0 below.** The change broke this; it's now fixed.
3. **No rounding or currency changes.** Not affected by the change, but I added checks for it.

**Checks added**
- `test_discount.py`: a below-threshold test using 99.99, 99, 50 and 0, which should all give no discount.
- `test_shipping.py`: values near and away from the boundary (49.99, 50.01, 100, 0) to catch rounding and inclusive/exclusive mistakes.
- `VERIFY.md`: says what each test covers, notes that the two thresholds must stay independent, and gives a single command to run everything: `python -B -m unittest test_shipping.py test_discount.py`.

**Rejection evidence**
- Against the changed code before my fix, the new discount test failed: `discount(99.99)` returned 10 instead of 0 (`AssertionError: 10 != 0 : discount mismatch`). The shipping tests passed, as expected.
- I then broke the fixed code on purpose, one way at a time, each in a clean temporary copy. My first attempt gave confusing results because each run picked up a cached copy of the module; with the cache turned off, every broken version failed the test you'd expect:

| Deliberate break | Failing test |
|---|---|
| Shipping threshold back to 100 (the old value) | `test_shipping` and `test_shipping_no_rounding` (`5 != 0`) |
| Shipping `>=` changed to `>` | `test_shipping` |
| Discount `>=` changed to `>` | `test_discount` (`0 != 10`) |
| Discount threshold set to 50 (the regression) | `test_discount_below_threshold` (`10 != 0`) |
| `round()` applied in `shipping_fee` | `test_shipping_no_rounding` (`0 != 5`) |
| `round()` applied in `discount` | `test_discount_below_threshold` (`10 != 0`) |

**Coverage limits**
- The tests check specific values only, not every possible amount.
- The spec doesn't say what should happen with negative amounts, non-numbers, `Decimal` values or currency, so none of that is tested.
- The rounding checks only catch rounding to whole numbers. Rounding to 2 decimal places, for example, wouldn't be caught.
- With no Git history, I could only check against `change.diff` and the current files.
- I didn't touch anything outside `commerce.py`, the two test files and `VERIFY.md`.