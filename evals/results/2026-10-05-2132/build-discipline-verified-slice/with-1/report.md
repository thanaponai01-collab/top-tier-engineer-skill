The checkout fee is in. `python checkout.py` now prints `110` (it printed `100` before), and `run --strict` followed by `status` reports `VERIFY-STATE: green`. Nothing was committed, pushed or deployed.

**The change:** `fixture/app.py` now has `FEE_CENTS = 10`, and `total(cents)` returns `cents + FEE_CENTS`. That matches SPEC.md: a fixed 10-cent fee added to the price.

**Evidence**
- **Rejection, before the fix:** both checks failed with `AssertionError: '100' != '110' : expected checkout output 110, got 100`, and the existing unit test failed with `100 != 110`. The helper kept this output as a receipt in `.verify-state.json`.
- **Passing, after the fix:** `PASS run python -m unittest tests.test_checkout_entry`. The summary was `2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests`.
- **Entry-point check:** new `tests/test_checkout_entry.py` runs `python checkout.py` as a subprocess and expects `110`, taken from SPEC.md (100 + 10).
- **Recipe:** `VERIFY.md` has a "Checkout fee" section and keeps the live-gateway blind spot. I froze the checks and SPEC.md with `baseline` before touching `app.py`.
- **Log:** `BUILD.md` records the slice as proven and uncommitted, with one deferred item.

**Coverage limits**
- The entry point only exercises one input, because `checkout.py` hardcodes `total(100)`. Other amounts such as 0 or 250 have no check. That is the deferred item in `BUILD.md`, due once `checkout.py` takes an amount.
- The live payment gateway is not covered, as the existing MANUAL note says. I kept that note.
- Strict green covers only the mapped checks. I did not run a separate mutation challenge. The retained receipt is from the original defect.
- `VERIFY.md` has no `## Run` section, which is fine here because the check is a plain subprocess with nothing to start.

<!-- file written by the agent: fixture/BUILD.md -->
# Build

- Checkout fee (+10 cents): `python checkout.py` prints `110`; `python -m unittest discover tests` OK | proven | uncommitted (not asked to commit)

## Deferred
- Fee on amounts other than 100 through the entry point | checkout.py takes no input | due when checkout.py accepts an amount: add a test for e.g. 0 -> 10
