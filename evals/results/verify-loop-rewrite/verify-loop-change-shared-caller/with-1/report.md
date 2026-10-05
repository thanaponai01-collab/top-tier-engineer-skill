**Verdict:** the change had a regression, now fixed. `run --strict` and `status` print `VERIFY-STATE: green` on 2 features and 4 tests, with the checks frozen by `baseline`.

**Affected claims**
- **Shipping** (SPEC line 1): the change to 50 is correct. `shipping_fee(50)` is 0 and `shipping_fee(49)` is 5.
- **Discount** (SPEC line 2): the change broke this. `discount` shared `QUALIFY`, so `discount(50)` through `discount(99)` returned 10 instead of 0.

**Fix:** in `commerce.py` I split `QUALIFY` into `SHIPPING_QUALIFY = 50` and `DISCOUNT_QUALIFY = 100`. Behaviour at and above 100 is unchanged, and there is no rounding or currency handling.

**Checks added**
- `test_discount.py`: `test_no_discount_below_100` covers 99, 50 and 49 → 0. The old test only used 100 and 101, so the regression passed it.
- `test_shipping.py`: `test_shipping_above_threshold` covers 100 → 0 and 0 → 5. This is an extra case I added.
- `VERIFY.md`: I added `fail-proof:` notes to both sections.

**Rejection evidence (observed)**
- **Regression state:** with the shared 50 threshold, Discount went red with `AssertionError: 10 != 0 : discount mismatch`.
- **Shipping at the old threshold:** with `SHIPPING_QUALIFY` set back to 100, Shipping went red with `5 != 0 : shipping fee mismatch`.
- **Restored code:** both checks pass again.

**Adjacent regressions checked:** discount at and above 100, and shipping on both sides of 50 and at 100.

**Coverage limits**
- Only these two functions are covered. No other callers exist in the folder, and there is no real-run or app-level check.
- Non-integer and negative totals are untested, and the spec doesn't define them.
- With no Git history, I used `change.diff` and manual restores of `commerce.py`. The final strict green rests on the baseline of 5 files, which covers `commerce.py` and the check files.
- I never edited any existing assertion; I only added test methods, so those two test files need a person's review.