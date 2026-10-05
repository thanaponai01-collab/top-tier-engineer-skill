The checkout fee is fixed. `python checkout.py` now prints 110, and `verify.py run --strict` followed by `status` reports `VERIFY-STATE: green`. Nothing was committed, pushed or deployed.

**Root cause (proven):** `fixture/app.py:2` had `return cents + 11`. SPEC.md says the fee is a fixed 10 cents, so the total for 100 cents should be 110.

**Proof in both directions:**
- **Cause present:** `python checkout.py` printed `111`, and the existing `test_total` failed with `111 != 110`.
- **Only the cause removed:** in a scratch copy I changed just `11` to `10`. The output was `110` and the tests passed. I deleted the scratch copy.

**Why it wasn't caught:** `test_total` did fail, but nothing mapped it into a retained check, and nothing exercised `checkout.py`. `VERIFY.md` held only the blind-spot note.

**Experiments:** the cause was proven on the first hypothesis, so there were no dead ends.

| Hypothesis | Experiment | Result |
|---|---|---|
| The fee constant is wrong | Change only `11` to `10` in a scratch copy | Output 110, tests pass: confirmed |

**Files changed:**
- **`app.py`:** `11` changed to `10`.
- **`tests/test_checkout_entry.py`:** new test that runs `checkout.py` as a subprocess and expects `110` (100 plus the 10-cent fee from SPEC.md).
- **`VERIFY.md`:** added a "Checkout fee" section with `oracle: SPEC.md` and `fail-signal: expected checkout total 110, got 111`. The live-gateway blind spot is preserved.
- **`.verify-state.json`:** new, written by the helper. It holds the rejection receipt and baseline.

**Retained evidence:**
- **Rejection:** with `app.py` still on `+ 11`, `verify.py run` showed both tests failing (`FAILED (failures=2)`), and `.verify-state.json` holds the receipt.
- **Pass:** after the fix and a `baseline`, `run --strict` printed `1 checks pass, 0 fail | 0 unproven | 0 orphan tests`, and `status` printed `VERIFY-STATE: green`.
- **Test map:** `verify.py tests --strict` found 2 tests, both mapped, none unable to fail.

**Coverage limits:**
- `checkout.py` hardcodes a price of 100, so the entry-point check covers only that one input. Other amounts are exercised only through `total()` directly, and only at 100 as well.
- The live payment gateway is unverified. It is still listed as a manual blind spot.
- I did not run `verify.py challenge`. The rejection receipt comes from the real pre-fix bug rather than a reintroduced mutation.
- The strict-green result covers only the one mapped "Checkout fee" feature.

I did not check `fixture/` for `__pycache__` cleanup; there is a `__pycache__` folder from the test runs.