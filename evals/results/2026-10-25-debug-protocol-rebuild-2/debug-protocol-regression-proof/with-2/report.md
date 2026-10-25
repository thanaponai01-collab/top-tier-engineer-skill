The checkout overcharged by 1 cent because `app.total` added an 11-cent fee instead of the 10 cents SPEC.md requires. I changed that one line, added a regression test that runs the real checkout, and the debug-protocol gate now reports `DEBUG-GATE: done (1 proven of 1 experiments, fixed and held)`.

**Failure:** `python checkout.py` printed `111` where it should print `110`. SPEC.md says checkout adds a fixed 10-cent fee, so 100 + 10 = 110.

**Cause, proven both ways:** `fixture/app.py:2` in `total` read `return cents + 11`.
- **With that line:** `python checkout.py` printed `111`. This was run in a throwaway copy before any code was changed; the original files are kept in `.debug/before/`.
- **With only that line changed to `return cents + 10`:** it printed `110`.

**Why it wasn't caught:** the existing test in `tests/test_total.py` already failed on the broken code (`FAILED (failures=1)`), so the bug was visible to anyone running the suite. Nothing was acting on that failure. That test also only calls `total(100)` directly; nothing checked what `checkout.py` actually prints.

**Changes:**
- **`app.py:2`:** now `return cents + 10`.
- **`tests/test_checkout.py` (new):** runs `checkout.py` as a subprocess and checks that it prints `110`. The expected value comes from SPEC.md, not from the code.
- **`VERIFY.md`:** added a "Checkout fee" section that maps `app.py` to the test suite, with SPEC.md as the reference. The existing blind-spot note about the live payment gateway is unchanged, as AGENTS.md asks.

**Evidence kept in `fixture/.debug/state.json`:**
- **Rejection:** with the 11-cent line put back, `python -m unittest discover tests` fails both tests (`FAILED (failures=2)`, exit 1).
- **Passing:** with the fix it passes (`Ran 2 tests ... OK`), and `python checkout.py` prints `110`.

The skill says to commit `.debug/` with a fix. You said not to commit (and this isn't a git repo), so it's left in place uncommitted.

**Coverage limits:**
- Only a price of 100 cents is tested. Zero, very large or non-integer amounts are never tried; AGENTS.md says amounts are integer cents.
- The live payment gateway is outside this project and was not exercised.
- Nothing was committed, pushed or deployed.

<!-- file written by the agent: fixture/.debug/before/VERIFY.md -->
# Checks

## Blind spots
- MANUAL: live payment gateway is outside this local project.
