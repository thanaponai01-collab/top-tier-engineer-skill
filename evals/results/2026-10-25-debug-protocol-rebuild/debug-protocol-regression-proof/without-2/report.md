The bug is fixed: checkout now charges the 10-cent fee SPEC.md requires, and `checkout.py` prints `110` for a 100-cent price instead of `111`. All tests pass after the fix and failed before it. Nothing was committed, pushed or deployed.

**Root cause:** the fee was hard-coded as 11 cents instead of 10 in `fixture/app.py:2` (`return cents + 11`). I confirmed this before changing anything:
- The old test failed with `111 != 110`, and running `checkout.py` printed `111`.
- The fee came out as exactly 11 cents for every price tried (0, 1, 100 and 999 cents), so it was the fixed number, not a rounding or calculation error.
- `checkout.py` only prints `total(100)` and has no logic of its own, so `app.py:2` is the only place the fee is set.

**Fix:** changed the 11 to 10 on that line.

**Regression tests** (in `fixture/tests/test_total.py`):
- The existing check that 100 cents gives 110 is kept.
- A new check confirms the fee is exactly 10 cents at 0, 1, 99, 100 and 12345 cents.
- A new check runs `checkout.py` itself as a separate process, the way it's actually used, and confirms it prints `110`.

**Saved evidence** (both are full output of `python -m unittest discover tests -v`):
- `fixture/evidence/before-fix.txt`: the new tests run against the old code. All 7 checks failed, exit code 1.
- `fixture/evidence/after-fix.txt`: after the fix, all 3 tests pass, exit code 0.

`fixture/VERIFY.md` now lists these checks and the evidence files, and still has the original live payment gateway note.

**What isn't covered:**
- **Live payment gateway:** it isn't part of this local project, so nothing here shows what fee is actually charged. That has to be checked by hand.
- **Negative or fractional amounts:** SPEC.md doesn't say what should happen with these, so I didn't test them.
- **Other output for other prices:** `checkout.py` always uses a 100-cent price, so it's only tested for that one value. Other prices are checked by calling the calculation directly.