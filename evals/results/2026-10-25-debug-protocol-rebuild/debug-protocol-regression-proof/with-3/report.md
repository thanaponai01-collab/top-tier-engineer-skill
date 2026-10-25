I fixed the checkout fee: `python checkout.py` now prints `110` instead of `111`. The cause was a single line, and the regression check fails on the old code and passes on the fixed code.

**What was wrong:** `python checkout.py` printed `111` for a 100-cent price. `SPEC.md` says the fee is a fixed 10 cents, so the right output is `110`.

**Cause, proven both ways:** `fixture/app.py:2` was `return cents + 11`, adding 11 cents instead of 10.
- With that line as it was, `python checkout.py` prints `111`.
- With only that line changed to `return cents + 10` (in a throwaway copy), it prints `110`.

**Why it wasn't caught:** the existing test `tests/test_total.py` (`total(100) == 110`) already failed on the broken code (`FAILED (failures=1)`). The bug was visible; the red test just wasn't acted on. That test only calls `total()` directly and never ran the actual checkout script.

**Fix and regression evidence:**
- `app.py:2` now adds 10 cents.
- New test `tests/test_checkout_entry.py` runs `checkout.py` as a separate process and expects it to print `110`, as `SPEC.md` requires.
- Rejection: with the old `app.py` put back, `python -m unittest discover tests -v` failed with `FAILED (failures=2)`, so both tests catch the bug.
- Passing: on the fixed code both tests pass (`Ran 2 tests ... OK`).
- `VERIFY.md` has a new "Checkout fee" section pointing at `app.py` with this test command. The live-gateway blind-spot note is kept unchanged, as `AGENTS.md` asks.
- The run records are in `fixture/.debug/`: the original code in `.debug/before/`, plus the experiment and regression results. Nothing was committed, pushed or deployed.

**Coverage limits:**
- The live payment gateway was not exercised. It is outside this project, as `VERIFY.md` notes.
- Only one price (100 cents) is tested, because `checkout.py` hard-codes it and `SPEC.md` gives no other cases. Other amounts, zero, negative or non-integer inputs are untested, and `SPEC.md` doesn't say what they should do.
- The entry-point test assumes the price stays hard-coded at 100 in `checkout.py`. If the script starts taking input, the test will need updating.

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
