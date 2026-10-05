**Verdict:** `change.diff` introduced a regression, and I fixed it. `verify.py status` now prints `VERIFY-STATE: green`, after `run --strict` and `baseline`. `tests --strict` shows 3 tests, none flagged.

**The regression.** The diff changed the shared constant `QUALIFY` from 100 to 50. That moved the free-shipping threshold to 50 as the spec asks. It also moved the discount threshold, so `discount(50..99)` started returning 10. SPEC.md line 2 says it must stay 0 below 100. The existing discount test only covered 100 and 101, so it stayed green and missed this.

**Fix** (`commerce.py`): I split the shared constant into `FREE_SHIPPING_MIN = 50` and `DISCOUNT_MIN = 100`. The behaviour is now:
- Shipping is free at a subtotal of 50 or more and costs 5 below that.
- The discount is 10 at 100 or more and 0 below that.

**Affected claims**
- **Shipping:** the fee is 0 at 50 or more and 5 below. This still holds.
- **Discount:** it is 0 below 100. This was broken and is now fixed.
- **Amounts:** no rounding or currency change. The code never touches the amounts, and no check covers this claim.

**Adjacent regression checked.** The discount threshold was the other caller of the shared constant, and it was the one that broke.

**Rejection evidence**
- I added `test_no_discount_below_threshold` to `test_discount.py` (checks 99, 50 and 0) and ran it against the changed code. It failed with `AssertionError: 10 != 0 : discount mismatch`.
- I ran `verify.py challenge` on both features with `DISCOUNT_MIN = 50` and `FREE_SHIPPING_MIN = 100`. Each was rejected with the declared fail-signal, and `0 unproven` was reported afterwards.
- The mutation files are in `.verify-evidence/`.

**Files changed**
- `commerce.py` (the fix).
- `test_discount.py` (new test, additive).
- `VERIFY.md` (oracle and fail-proof lines).
- `.verify-evidence/` (new, holds the mutation files).
- I also ran `baseline`, so the state files are new.

I did not touch `SPEC.md`, `change.diff` or `test_shipping.py`.

**Coverage limits**
- The checks are unit-level with no real-run driver, and there is no app here to drive.
- Boundaries are tested only at the points listed: shipping at 49 and 50, discount at 0, 50, 99, 100 and 101.
- Non-integer, negative and non-numeric inputs aren't tested.
- The rounding/currency claim has no check.
- There is no git history, so the change boundary is `change.diff` only.