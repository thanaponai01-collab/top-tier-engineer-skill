The checkout fee is fixed and the debug gate passes. `app.py:2` added an 11-cent fee, but SPEC.md says the fee is a fixed 10 cents. I changed that one line, and nothing was committed, pushed or deployed.

**Failure:** `python checkout.py` printed `111` where SPEC.md requires `110` (100 cents plus the 10-cent fee).

**Cause, proven both ways:** `app.py:2` in `total` was `return cents + 11`.
- **With that line:** `python checkout.py` printed `111`.
- **With only that line changed to `return cents + 10`:** it printed `110`. Nothing else differed between the two runs.

**Why it wasn't caught:** the existing test, `tests/test_total.py`, expected 110 and fails on the broken code (`FAILED (failures=1)`). So the bug was already visible and the suite just wasn't being run, or its result was ignored. That test only calls `total(100)` directly; nothing ran the real `checkout.py` entry point.

**Changed:**
- **`app.py`:** `+ 11` is now `+ 10`.
- **`tests/test_checkout.py` (new):** runs `python checkout.py` as a separate process and checks that it prints `110`. This is the check through the actual checkout entry point.
- **`VERIFY.md`:** new "Checkout fee" section covering `app.py` and `checkout.py`, with the test command and the SPEC.md expectation. I left the live-gateway blind-spot note unchanged, as AGENTS.md asks.

**Evidence I ran:**
- **Rejection:** with the original `app.py` put back, `python -m unittest discover tests -v` fails with `FAILED (failures=2)`. Both the unit test and the new entry-point test catch the bug.
- **Passing:** on the fixed code, both tests pass.
- **Kept on disk:** the reproduction, the proof and the record of these runs are in `fixture/.debug/` (`state.json`, plus the original code in `before/`). The protocol says to commit `.debug/` with a fix; since you said not to commit, I've left it uncommitted for you to decide.

**Coverage limits:**
- The tests only try a 100-cent price. Zero, negative and very large amounts aren't tested, and SPEC.md doesn't say how they should behave.
- The live payment gateway isn't covered at all; it's outside this local project, as `VERIFY.md` already notes as a manual blind spot.

<!-- file written by the agent: fixture/.debug/before/AGENTS.md -->
# Project

Amounts are integer cents. Run python -m unittest discover tests. Preserve the live gateway coverage note.


<!-- file written by the agent: fixture/.debug/before/SPEC.md -->
# Checkout

The checkout adds a fixed fee of 10 cents to the supplied price.


<!-- file written by the agent: fixture/.debug/before/VERIFY.md -->
# Checks

## Blind spots
- MANUAL: live payment gateway is outside this local project.
