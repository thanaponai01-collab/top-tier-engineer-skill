The fee was wrong because `total()` in `app.py` added 11 cents instead of the 10 cents SPEC.md calls for. That line is now fixed, a new test runs the actual checkout script, and the debug-protocol gate passes all three stages.

**What was wrong:** `python checkout.py` printed `111`. SPEC.md says "a fixed fee of 10 cents", so for a price of 100 it should print `110`.

**Root cause, proven both ways:** `fixture/app.py:2`, `return cents + 11`.
- **With the line as it was:** the checkout script prints `111`, run in a throwaway copy before any code changed.
- **With only that line changed to `return cents + 10`:** it prints `110`.

One experiment was run and it confirmed the cause; there were no dead ends. The broken code is saved in `fixture/.debug/before/` and every run is logged in `fixture/.debug/state.json`.

**Why it wasn't caught:** it was. The existing `tests/test_total.py` asserts `total(100) == 110` and failed on the broken code. Either the tests weren't being run, or the failure was ignored. That test only calls `total()` directly and never runs `checkout.py`, so it would miss a fee bug added on the checkout path itself.

**Changes:**
- **`app.py`:** `+ 11` → `+ 10`.
- **New `tests/test_checkout_entry.py`:** runs `checkout.py` as a subprocess and expects `110`. The expected value is taken from SPEC.md, not from the code.
- **`VERIFY.md`:** added a "Checkout fee" section covering `app.py` and `checkout.py`, with the test command, SPEC.md as the reference, and the failure messages to look for. The existing note about the live payment gateway is unchanged.

**Evidence that the test catches the bug:**
- With the old `app.py` put back, `python -m unittest discover tests` failed with 2 failures: the new entry-point test and the original one.
- On the fixed code, both tests pass. I also ran `python checkout.py` myself and it printed `110`.

**Coverage limits:**
- **Live payment gateway:** outside this local project, as VERIFY.md already says. Nothing here shows the gateway charges `110`.
- **Only one price is tested:** 100 cents. Zero, negative, non-integer or very large amounts are untested, and SPEC.md doesn't say what should happen with them.
- **No fee configuration:** the fee is still a hard-coded constant, so these checks would also accept a wrong value that someone sets to 10 on purpose somewhere else.

Nothing was committed, pushed or deployed. `fixture/.debug/` is still there as evidence. The skill says to commit it alongside the fix, so keep it if you commit, or delete it.

<!-- file written by the agent: fixture/.debug/before/VERIFY.md -->
# Checks

## Blind spots
- MANUAL: live payment gateway is outside this local project.
