I found and fixed the bug. Checkout charged an 11-cent fee instead of the 10 cents in SPEC.md, and the helper's gate now reports `DEBUG-GATE: done (1 proven of 1 experiments, fixed and held)`.

**Failure:** `python checkout.py` printed `111`. SPEC.md says checkout adds a fixed 10-cent fee, so a price of 100 should give `110`.

**Root cause, proven both ways:** `app.py:2` in `total` was `return cents + 11`.
- **With that line as it was:** checkout printed `111`.
- **With only that line changed to `return cents + 10`:** checkout printed `110`.

The helper made both runs on copies of the original code, and that code is kept in `.debug/before/`.

**Why it wasn't caught:** the existing test `tests/test_total.py` already expected 110 and failed on the broken code. So the bug was visible; the failing suite just wasn't acted on. That test only calls `total(100)` directly. Nothing tested the actual `checkout.py` entry point, and no price other than 100 was tried.

**Fix and evidence:**
- `app.py`: the fee is now `+ 10`.
- **New test `tests/test_checkout.py`:** it runs `checkout.py` as a separate process and checks the printed output is `110`, which is the value from SPEC.md.
- **`VERIFY.md`:** added a "Checkout fee" section covering `app.py` and `checkout.py` with the test command. I kept the live-gateway blind-spot note, as AGENTS.md asks.
- **Failing on the broken code:** with the original `app.py` put back, `python -m unittest discover tests` failed with 2 failures, the old unit test and the new entry-point test.
- **Passing on the fix:** it now passes, 2 tests OK, and `checkout.py` prints `110`.

**Not covered:**
- The live payment gateway; it's outside this local project and stays a manual check per `VERIFY.md`.
- Prices other than 100, because `checkout.py` hard-codes `total(100)`. The fix is a constant, so other prices should be fine, but nothing tests them.
- Real currency or rounding behaviour, since all amounts are integer cents.

Nothing was committed, pushed or deployed. `.debug/` holds the debugging record and should be committed along with the fix.

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
