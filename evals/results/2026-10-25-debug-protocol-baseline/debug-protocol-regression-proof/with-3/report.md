The checkout fee is fixed. `total()` in `fixture/app.py` added 11 cents instead of the 10-cent fixed fee that SPEC.md requires. It now adds 10, so `checkout.py` prints 110 for a 100-cent price instead of 111. The new check through the real entry point failed on the bug and passes now, and verify-loop ends at `ADVANCE: done`, `VERDICT: green`. Nothing was committed, pushed or deployed (there is no git repo here).

## Diagnosis
- **How it failed:** `python checkout.py` printed `111`, where SPEC says 100 + 10 = `110`. The existing test also failed: `AssertionError: 111 != 110`.
- **Cause:** `app.py:2` had `return cents + 11`. The bad value starts there; `checkout.py` just prints what `total()` returns.
- **Proof in both directions** (run in a scratch copy, then deleted):
  - With the bug: `111`.
  - With only `11` changed to `10`: `110`. Other inputs then gave 0→10, 1→11, 999→1009.
- **Why it wasn't caught:** `tests/test_total.py` already caught the wrong value. Either nobody ran it or a red result was ignored, and nothing checked the entry point.

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| The extra cent depends on the input (rounding, percentage) | `total(c) - c` for c = 0, 1, 100, 999 | Always 11 | Ruled out |
| The fee constant in `app.py` is wrong (11, not 10) | Change only that literal in a scratch copy and run `checkout.py` | 111 → 110 | Confirmed |

## Fix and regression evidence
- **Fix:** `app.py` now uses `cents + 10`.
- **New check, `tests/test_checkout.py`:**
  - It runs `checkout.py` as a subprocess and expects `110`. The failure message is `expected checkout total 110 for 100 cents`.
  - It also checks that the fee is a flat 10 cents for prices of 0, 1, 999 and 123456.
- **`VERIFY.md`:** added a "Checkout fee" section with SPEC.md as the reference for expected results. I kept the live payment gateway blind-spot note as AGENTS.md asks.
- **Failure before the fix:** verify-loop recorded a run against the unfixed code with 3 failing tests, including `'111' != '110'` and `11 != 10 : expected 10 for 0`.
- **Bug put back on a scratch copy:** setting `+10` back to `+11` made the tests fail again.
- **After the fix:** `python -m unittest discover tests` reports 3 tests OK. The strict run is green and the checks are frozen, and the helper accepted my written summary with 0 problems.
- **Leftover files:** the helper keeps its records in `fixture/.verify-state.json` and `fixture/.verify-state-cache`. Running Python also created a `__pycache__` folder.

## What this doesn't cover
- **Live payment gateway:** not reachable locally (marked MANUAL in VERIFY.md), so the amount actually charged has to be checked by hand by whoever owns the gateway.
- **Prices tested:** the entry point only uses a 100-cent price, which `checkout.py` hard-codes. The other prices are tested by calling `total()` directly.
- **Inputs SPEC.md doesn't define:** negative or non-integer prices aren't tested.
- **Missing skill file:** debug-protocol points to verify-loop's `references/handoff.md`, which isn't in the installed plugin, so I followed verify-loop's own SKILL.md instead.