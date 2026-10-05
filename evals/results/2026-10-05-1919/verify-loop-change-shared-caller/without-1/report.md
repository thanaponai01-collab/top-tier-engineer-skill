The change broke the discount rule, and I fixed it. With the fix in place, all 5 tests pass.

**Affected claims**
- **Shipping:** free from a subtotal of 50, inclusive, otherwise a fee of 5. This is the intended change, and it holds.
- **Discount:** 10 at 100 or above, 0 below. The change broke this. `discount` used the same `QUALIFY` constant that the diff moved to 50, so subtotals from 50 to 99 wrongly got a discount of 10.
- **No rounding:** the same amounts are used as given. It was not affected, and I added a test for it.

**Fix (`commerce.py`)**
- I split the shared constant into `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100`, so each rule has its own threshold.

**Checks added**
- `test_discount.py`: new test that totals 0, 49, 50, 75, 99 and 99.99 get no discount.
- `test_shipping.py`: new tests for 49.99 (fee 5), 50.01 (free) and 100 (free).
- `run_checks.sh`: runs both test files and exits non-zero on any failure. It is listed in `VERIFY.md` under a new "All" section.

**Rejection evidence**
- I ran the new tests against the changed `commerce.py` (`QUALIFY = 50`) in a scratch copy. 1 of 5 failed: `AssertionError: 10 != 0 : discount mismatch` in `test_below_threshold_has_no_discount`.
- The original tests could not have caught this. They only checked discount at 100 and 101.

**Adjacent checks**
- Shipping at 49, 49.99, 50, 50.01 and 100, and discount at 100 and 101, still pass.

**Coverage limits**
- Only the boundaries named above are tested; nothing property-based or exhaustive.
- Nothing is tested for negative or non-numeric inputs, because the spec doesn't define them.
- There is no CI hook; `run_checks.sh` has to be run by hand.
- `change.diff` is not applied or tracked here (there is no Git history), so the changed version was reconstructed from the diff and my copy of the file.