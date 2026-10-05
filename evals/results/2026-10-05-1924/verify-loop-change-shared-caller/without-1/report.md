I fixed the regression. The change set the shared `QUALIFY` to 50, which also made `discount` return 10 at subtotals of 50–99. The spec says the discount stays at 100. All 4 tests now pass, and they are `unittest` tests so VERIFY.md's commands still work.

**Affected claims**
- **Free shipping at 50 or more, fee 5 below:** the change meets this, and it still holds after the fix.
- **Discount 10 at 100 or more, 0 below:** the change broke this, and the fix restores it.
- **No rounding or currency changes:** the fix leaves the amounts as given, with plain comparisons only.

**Fix** (`commerce.py`)
- `QUALIFY` is now two constants: `SHIPPING_QUALIFY = 50` and `DISCOUNT_QUALIFY = 100`.
- Shipping keeps the new threshold. The discount keeps its original one.

**Tests added**
- **`test_discount.py`:** subtotals 99, 99.99, 50 and 0 must give no discount.
- **`test_shipping.py`:** 49.99 and 0 must pay the fee, and 100 must ship free.

**Rejection evidence**
- I put the change's shared-constant `commerce.py` back temporarily and ran `test_discount.py`.
- It failed with `AssertionError: 10 != 0 : discount mismatch`, so the new check catches the regression.
- I then restored the fix and all 4 tests pass.

**Adjacent regressions checked**
- The only other function sharing the constant was `discount`, which is where the regression was.
- The shipping boundary at 49 and 50 is unchanged.
- I touched no other files.

**Coverage limits**
- The tests cover only boundary and sample values, not every input.
- They don't cover negative or non-numeric subtotals, because the spec doesn't define them.
- There is no Git history here, so `change.diff` was the only record of what changed.