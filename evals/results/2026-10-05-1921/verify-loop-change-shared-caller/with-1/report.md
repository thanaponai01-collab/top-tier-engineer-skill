**Verdict: the change introduced a regression, and I fixed it. `run --strict` is green and `status` prints `VERIFY-STATE: green`.**

**Comparison point:** there is no Git history, so I used `change.diff` (`QUALIFY` 100 → 50 in `commerce.py`).

**The regression:** `shipping_fee` and `discount` both read the one `QUALIFY` constant. Lowering it to 50 gave a discount of 10 at subtotals from 50 to 99, which SPEC.md says is 0 below 100.

**Fix:** `commerce.py` now has separate constants, `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100`. The intended shipping change is kept.

| Claim from SPEC.md | Check | Result |
|---|---|---|
| Free shipping from 50 inclusive, fee 5 below | `test_shipping.py`, with a new range test (0, 49, 49.99, 50, 50.01, 99, 100, 1000) | passes |
| Discount 10 at 100 or above | `test_discount.py` | passes |
| Discount 0 below 100, including 50 and 99 | new `test_discount_below_threshold` | passes |
| Amounts used as given, with no rounding | 49.99 and 50.01 in the shipping range test | passes |

**Rejection evidence:**
- **Discount on the changed code:** the new test failed with `AssertionError: 10 != 0 : discount mismatch`. This was a real `verify.py run` before the fix.
- **Shipping:** a scratch-copy mutation setting the shipping threshold to 100 was caught with `AssertionError: 5 != 0 : shipping fee mismatch`.
- **Discount after the fix:** a scratch-copy mutation setting the discount threshold to 50 was caught with `10 != 0 : discount mismatch`.
- `verify.py tests --strict` maps all 4 tests to a feature, with none lacking an assertion.

**Files I changed:**
- `commerce.py`: the fix.
- `test_discount.py` and `test_shipping.py`: added tests. The existing tests are unchanged, and I did this before freezing the baseline.
- `VERIFY.md`: added `oracle: SPEC.md` and `fail-proof:` lines to both features.
- `.verify-state.json`: created by the helper.

**Coverage limits:**
- Only the two functions and the spec's boundaries are covered.
- There are no negative or non-numeric inputs, because the spec doesn't define them.
- Nothing outside `fixture/` calls these functions, so no other callers were checked.
- Strict green covers only the checks mapped in `VERIFY.md`.