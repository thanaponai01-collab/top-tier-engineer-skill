**Verdict: FAIL.** Don't ship this. `fee(100)` returns 5, but SPEC criterion 1 says an order of 100 or more ships free. The green suite doesn't contradict this, because `test_hundred` asserts the wrong value.

**What's wrong (proven, I ran it):**
- `shipping.py:4` uses `total > 100`. The spec requires `>= 100`.
- `fee(100)` returns 5, and the spec says it should return 0. At exactly 100, customers would be charged a fee they shouldn't pay.
- `test_hundred` (`test_shipping.py:13-14`) asserts `fee(100) == 5`. It was written to match what the code does, not what the spec says. That is why 4 of 4 tests pass.

**Failure type:** logic error. The boundary is off by one, and the test that should catch it enforces the bug.

| Behavior | Oracle | Result | Evidence |
|---|---|---|---|
| Total ≥ 100 ships free | Spec 1 | **Fail** at exactly 100 (returns 5, should be 0) | proven |
| Total < 100 costs 5 | Spec 2 | Pass (0, 99.99 → 5) | proven |
| Negative total raises `ValueError` | Spec 3 | Pass (-0.01 and -1 raise) | proven |

**Not done:**
- **Mutations:** I skipped the mutation spot-check, since the gate already fails on a real spec violation. The suite is already known to miss this boundary mutation (`>=` vs `>`).
- **Concurrency and scale:** I didn't test these. The function is pure, so concurrency doesn't apply.
- **Other inputs:** non-numeric input and `None` are outside the spec.

**Fix needed (not applied, since the gate judges and doesn't fix):**
1. Change `>` to `>=` in `shipping.py:4`.
2. Change `test_hundred` to expect 0. This follows the spec, so it doesn't weaken the oracle. If 100 is meant to pay the fee, the spec is what's wrong, and the owner has to change it.

I can make both edits and re-run if you want.