**Verdict: green.** The change introduced a regression, which I fixed. `run --strict` and then `status` print `VERIFY-STATE: green`.

**Comparison point:** there is no Git history, so I used `change.diff`. It sets `QUALIFY` from 100 to 50 in `commerce.py`.

**Regression:** `shipping_fee` and `discount` both read the one `QUALIFY` constant. Lowering it for shipping also dropped the discount threshold from 100 to 50. That violates the spec line "discount remains 10 at 100 or above, 0 below". I split it into `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100` in `commerce.py`.

| Claim (SPEC) | Check | Result |
|---|---|---|
| Free shipping at 50 or more (inclusive), fee 5 below | `test_shipping.py` (50→0, 49→5) | pass |
| Discount 10 at 100 or more, 0 below (adjacent regression) | `test_discount.py` | pass |
| No rounding or currency changes | no check | gap |

**Check repair:** `test_discount.py` passed on the regressed code because it only tested 100 and 101. I added `test_discount_below_threshold`, which checks 99, 50 and 0 → 0. Run against the regressed code before the fix, it failed with `10 != 0 : discount mismatch`. No existing expectations were changed.

**Rejection evidence:** both challenges were caught by their declared signals.
- **Discount:** a mutation made `discount` use the shipping threshold. The result was `AssertionError: 10 != 0 : discount mismatch`.
- **Shipping:** a mutation changed `>=` to `>`. The result was `AssertionError: 5 != 0 : shipping fee mismatch`.

**Files changed:**
- Product: `commerce.py`.
- Check: `test_discount.py`.
- Recipe: `VERIFY.md` now has `fail-proof:` notes.
- Added: `mutation.json` and `mutation_shipping.json`, the two challenge mutations.

The `baseline` freeze recorded 5 check files, and `tests --strict` was clean (3 tests, none unmapped or unable to fail).

**Coverage limits:**
- The tests cover only the boundary values 0, 49, 50, 99, 100 and 101.
- Nothing checks the "no rounding" line, such as float or non-integer totals.
- Only one mutation per feature was tried.
- Strict green covers the mapped checks only.