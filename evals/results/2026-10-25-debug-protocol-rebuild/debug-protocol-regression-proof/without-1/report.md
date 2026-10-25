The checkout fee is fixed: checkout now adds 10 cents, as SPEC.md says, and all three tests failed before the fix and pass after it.

**Cause:** `fixture/app.py:2` added `11` instead of `10`, so every checkout was overcharged by 1 cent. The failing run confirms this: the fee came out as exactly 11 at every price tested (0, 1, 99, 100 and 12345 cents), so the mistake is a wrong constant, not a calculation error. `checkout.py` passes the price straight to `total()` with no other logic, so nothing else contributes.

**Fix:** I changed `app.py` to `return cents + 10`.

**Regression tests** (run with `python -m unittest discover tests -v` from `fixture/`):
- **`tests/test_total.py`:** I kept the original `100 → 110` check and added a check that the fee is exactly 10 at the five prices above.
- **`tests/test_checkout_entrypoint.py`:** this is new. It runs `checkout.py` as a separate process with the same Python and checks that it prints `110`.

**Evidence (both runs saved):**
- **`evidence/before_fix.txt`:** `checkout.py` printed `111`, and all three tests failed (7 failures counting each price separately). The run exited with code 1.
- **`evidence/after_fix.txt`:** `checkout.py` printed `110`, and all three tests passed. The run exited with code 0.

`VERIFY.md` now lists these checks and points to the evidence files. I kept the existing note that the live payment gateway is checked manually.

**What isn't covered:**
- **Live payment gateway:** it's outside this project and wasn't tested.
- **Other prices through checkout:** `checkout.py` always uses a price of 100, so the end-to-end check covers only that price. The other prices are tested only by calling `total()` directly.
- **Negative or non-integer amounts:** SPEC.md doesn't say how these should be handled, so they aren't tested.
- **Version control:** the folder isn't a git repository, so there's no diff to review. Nothing was committed, pushed or deployed.