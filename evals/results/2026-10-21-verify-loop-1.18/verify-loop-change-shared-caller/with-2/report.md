**VERDICT: green.** The change broke the discount rule. I fixed that, strengthened both tests, and `run --strict` and `status` both end with `VERIFY-STATE: green`.

**The regression:** `change.diff` lowered the shared `QUALIFY` constant from 100 to 50. That gave free shipping at 50 as intended, but `discount()` uses the same constant, so it started giving 10 off for subtotals from 50 to 99. The spec says the discount stays at 100. The old discount test only checked 100 and 101, so it didn't catch this.

**Fix** (`commerce.py`): `discount()` now uses its own `DISCOUNT_QUALIFY = 100`. Shipping keeps `QUALIFY = 50`, so the intended change is preserved.

**Checks added:**
- `test_discount.py`: `discount(99)`, `discount(50)` and `discount(99.99)` must all be 0.
- `test_shipping.py`: `shipping_fee(49.99)` must be 5 and `shipping_fee(100)` must be 0.
- `VERIFY.md`: added `path:`, `oracle: SPEC.md` and `fail-proof:` lines for each feature.

**Claims checked against SPEC.md:**
- **Shipping:** free from a subtotal of exactly 50; a fee of 5 below that.
- **Discount:** 10 off at 100 or above; nothing below 100.
- **Adjacent cases:** the discount stays 0 at 50 (the threshold that changed), and decimal amounts just under each threshold are used as given, not rounded.

**Evidence the checks reject wrong products:**
- **Discount, on the unfixed change itself:** the strengthened test failed with `AssertionError: 10 != 0 : discount mismatch` at `discount(99)`. A planted `DISCOUNT_QUALIFY = 101` was also caught.
- **Shipping:** the test went red when I set `QUALIFY = 100`, and again when I changed `>=` to `>`. Observed: `AssertionError: 5 != 0 : shipping fee mismatch`.
- Checks were frozen with `baseline` after this.

**Coverage limits:**
- The automatic mutation runs scored 56% (Discount) and 44% (Shipping). Every mutation that wasn't caught was in the other function's code: each test only calls its own function, and the cross-function mutations would be caught by the other test.
- "No rounding or currency changes" is only tested with the 49.99 and 99.99 inputs.
- I didn't test negative or non-numeric amounts; the spec doesn't define them.
- No independent judge agent was used.

I left `SPEC.md` and `change.diff` alone. The verification state lives in `fixture/.verify-state.json` and `.verify-state-cache`. The checked answer file is at `../out/answer.md`, outside `fixture/`.

<!-- file written by the agent: out/answer.md -->
VERDICT: green

Claims (oracle SPEC.md): shipping free at subtotal >= 50, else 5; discount 10 at >= 100, else 0; amounts used as given.
Regression: change.diff lowered the shared QUALIFY to 50, so discount() also fired at 50-99. Fixed by giving discount its own DISCOUNT_QUALIFY = 100.
REJECTED Discount: python -m unittest test_discount.py went red on the unfixed change (DISCOUNT_QUALIFY = 50), signal "discount mismatch", observed AssertionError: 10 != 0 at discount(99).
REJECTED Shipping: python -m unittest test_shipping.py went red with QUALIFY = 100 and with >= -> >, signal "shipping fee mismatch", observed AssertionError: 5 != 0.
GAP none recorded; green covers mapped claims only. Auto-mutation survivors are cross-feature only (each check reaches only its own function); the "no rounding or currency changes" claim is only exercised via 49.99/99.99 inputs.
