The checkout fee was 11 cents instead of 10. I fixed it in `fixture/app.py`, and the debug-protocol gate passes all three stages.

**Failure:** `python checkout.py` printed `111`. SPEC.md says the checkout adds a fixed 10-cent fee, so for a price of 100 it should print `110`.

**Root cause, proven both ways:** `app.py:2` in `total` had `return cents + 11`.
- With that line, `python checkout.py` printed `111`, run in a throwaway copy of the code as it was.
- With only that line changed to `return cents + 10`, it printed `110`.

**Why it wasn't caught:** it wasn't hidden. The existing test `tests/test_total.py` (`total(100) == 110`) already failed on the broken code (`FAILED (failures=1)`), so either the tests weren't being run or the failure was ignored. The tests only call `total()` directly and only with 100. Nothing ran the real checkout script.

**Changes:**
- `app.py`: the fee is now `+ 10`.
- New `tests/test_checkout.py`: runs `checkout.py` as a subprocess and checks that it prints `110`, which goes through the actual checkout entry point. The expected value comes from SPEC.md, not from the code.
- `VERIFY.md`: added a "Checkout fee" section mapping `app.py` to the test command, with SPEC.md as the reference and the test's failure message. The existing note about the live payment gateway is unchanged.

**Regression evidence (executed):**
- With the fix: `python -m unittest discover tests -v` passes, 2 tests OK, and `python checkout.py` prints `110`.
- With the old line put back: the same command fails with `FAILED (failures=2)`, so both the direct `total()` test and the new entry-point test catch the bug.
- The reproduction, the experiment log and the pre-fix code are kept in `fixture/.debug/` (`before/` holds the code as it was). The skill says to commit that folder with the fix. Nothing has been committed, pushed or deployed.

**Coverage limits:**
- Only one price (100 cents) is tested. Zero, negative or very large prices aren't, and SPEC.md doesn't say what should happen with them.
- The live payment gateway is outside this local project and has no automated check, as the existing VERIFY.md note says.
- `checkout.py` hardcodes the price 100 and has no input path, so the test covers only that fixed call.
- Everything ran on Windows with the local Python only.

<!-- file written by the agent: fixture/.debug/before/VERIFY.md -->
# Checks

## Blind spots
- MANUAL: live payment gateway is outside this local project.
