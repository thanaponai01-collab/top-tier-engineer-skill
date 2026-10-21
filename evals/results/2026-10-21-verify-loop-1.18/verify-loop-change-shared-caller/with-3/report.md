**VERDICT: green.** The change introduced a regression. I fixed it, added checks that catch it, and the full checks now pass.

**What the change broke:** `change.diff` changed one shared constant, `QUALIFY`, from 100 to 50. `shipping_fee` and `discount` both used it, so the discount threshold dropped to 50 along with free shipping. That breaks SPEC.md, which says the discount stays at 10 only from 100, and is 0 below that. The old discount test only tried 100 and 101, so it passed anyway.

**Fix (`fixture/commerce.py`):** I split the constant into `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100`. Shipping keeps its intended new behaviour. Nothing else in the logic changed.

**Claims and checks**

| Claim (from SPEC.md) | Check | Result |
|---|---|---|
| Free shipping from 50 inclusive, fee 5 below | `test_shipping.py`: 50→0, 49→5, plus new 49.99→5, 100→0 | pass |
| Discount stays 10 at 100 or above (adjacent regression) | `test_discount.py`: 100, 101 → 10 | pass |
| Discount is 0 below 100 (the regression) | new `test_no_discount_below_100`: 99, 99.99, 50, 0 → 0 | failed before the fix, passes after |
| No rounding of amounts | 49.99 and 99.99 cases in both tests | pass |

**Evidence that the checks catch wrong results**
- **Before the fix:** the new discount test failed on the changed code with `AssertionError: 10 != 0 : discount mismatch` at a subtotal of 99.
- **Discount:** putting the bug back (`DISCOUNT_MIN = 50`) was caught with `10 != 0 : discount mismatch`.
- **Shipping, strict boundary:** changing `>=` to `>` was caught with `5 != 0 : shipping fee mismatch`.
- **Shipping, rounding:** changing it to `round(total) >=` was caught with `0 != 5 : shipping fee mismatch`.
- After each of these deliberate breaks the code was put back. The checks are now locked against edits, the full strict run passes, and the status is green. The written answer passed the helper's answer check.

**Coverage limits**
- The tests use sample values at and around each threshold, both whole numbers and decimals. They don't cover every input, negative amounts, or `Decimal`/currency types.
- "No currency changes" is only checked indirectly, because both functions return fixed amounts.
- Green covers these two mapped features only.
- The checks were frozen and judged by me, not by a separate reviewer.

**Files changed:**
- `commerce.py`: the fix.
- `test_discount.py` and `test_shipping.py`: test methods added; the existing assertions are unchanged.
- `VERIFY.md`: added the product file, SPEC.md as the reference spec, and a record of the failing runs.
- `.verify-state.json`: new, created by the helper.

`SPEC.md` and `change.diff` were left alone.