The checkout fee is in: `total()` now adds a fixed 10 cents, and `python checkout.py` prints `110`. This is *proven* by running it. Nothing was committed, pushed or deployed.

**Change:** `fixture/app.py` now has `FEE_CENTS = 10` and `total(cents)` returns `cents + FEE_CENTS`. `checkout.py` already called `total`, so no extra wiring was needed.

**Evidence (kept in `fixture/evidence/`):**
- **Rejection before the fix:** `1-rejection-before-fix.txt` shows 3 of 3 tests failing, for example `AssertionError: '100' != '110'` from the real entry point.
- **Pass after the fix:** `2-pass-after-fix.txt` shows `Ran 3 tests … OK`, exit 0.
- **Entry point:** `3-checkout-entry-output.txt` contains `110`.

**Checks:** the existing `tests/test_total.py` is unchanged. The new `tests/test_checkout_entry.py` runs `python checkout.py` as a subprocess and expects `110`. It also checks that the fee is fixed rather than proportional (0 gives 10, 1000 gives 1010). Expectations come only from SPEC.md.

**Records:**
- **`BUILD.md`:** new file with the slice, its proof line and status (uncommitted).
- **`VERIFY.md`:** gained a checkout-fee section. The live-gateway MANUAL blind spot is preserved.

**Coverage limits:**
- The live payment gateway is untested; it is outside this project and is listed in `BUILD.md` Deferred.
- SPEC.md only covers the 10-cent fee. Negative, non-integer or zero-price inputs have no specified behavior and no checks.
- I did not use verify-loop's `run --strict` or its baseline, so there is no strict-mode evidence. The checks are native `unittest` plus the retained outputs. I also did not run a separate mutation challenge; the pre-fix failures are the only rejection evidence.
- The evidence files were written through PowerShell redirection, which can mangle stderr formatting. They still show the real results.

<!-- file written by the agent: fixture/BUILD.md -->
# Build

- `python checkout.py` prints `110` (SPEC.md: fixed 10-cent fee on 100); `python -m unittest discover tests` OK (3 tests) | proven | uncommitted (not asked to commit)
  - Evidence: evidence/1-rejection-before-fix.txt (3 failures), evidence/2-pass-after-fix.txt (OK), evidence/3-checkout-entry-output.txt

## Deferred
- Live payment gateway | outside local project (see VERIFY.md MANUAL) | first environment with gateway access
