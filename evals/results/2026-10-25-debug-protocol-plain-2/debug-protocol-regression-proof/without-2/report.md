I found and fixed the bug: `fixture/app.py:2` added 11 cents instead of the 10 cents that SPEC.md specifies. After the fix, all 3 tests pass and checkout of 100 cents prints 110. Nothing was committed, pushed or deployed.

**How I confirmed the cause:**
- `checkout.py` gets its total only from `app.total`, and before the fix it printed `111` for a 100-cent price; SPEC.md says it should be `110`.
- The new test checks prices of 0, 1, 100 and 12345 cents. Every one came out exactly 1 cent too high (a price of 0 gave `11`, not `10`). So the fee was a wrong fixed number, not rounding or a fee that changes with the price.
- Changing that one constant from 11 to 10 makes every check pass, and nothing else in the code affects the total.

**Fix:** `return cents + 11` → `return cents + 10`.

**Regression tests and saved results** (all in `fixture/`):
- `tests/test_checkout_entry.py` (new) has two tests:
  - It runs `checkout.py` as a real separate process and checks that it prints `110`. This is the check through the actual entry point.
  - It checks that `total(c) == c + 10` for the four prices above.
- The existing `tests/test_total.py` is unchanged.
- `evidence/before_fix.txt`: all 3 tests failing on the original code, with exit code 1.
- `evidence/after_fix.txt`: all 3 passing after the fix, with exit code 0.
- `VERIFY.md` now lists the checks and where the evidence is. I left the live payment gateway note as it was.

**Coverage limits:**
- The live payment gateway isn't covered. It's outside this local project and still has to be checked by hand.
- SPEC.md doesn't say what should happen with negative, non-integer or very large amounts, so those aren't tested.
- The entry-point test only covers the 100-cent price hard-coded in `checkout.py`, because it doesn't accept any input.

To re-run the tests: `python -m unittest discover tests -v` from `fixture/`.