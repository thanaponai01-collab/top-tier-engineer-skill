I fixed the checkout fee: checkout now adds 10 cents instead of 11, and the tests that failed before the fix all pass now.

**Root cause:** in `app.py`, `total()` returned `cents + 11`, but SPEC.md says checkout adds a fixed fee of 10 cents. Before the fix I ran the tests at prices 0, 1, 100, 999 and 12345, and every result was exactly 1 cent too high (for example, 0 gave 11). An error that's the same 1 cent at every price means the fee number itself was wrong, not rounding or a percentage. Running `checkout.py` printed `111` instead of `110`.

**Fix:** `fixture/app.py` now uses a named constant, `FEE_CENTS = 10`, which `total()` adds to the price.

**Regression checks** (run with `python -m unittest discover tests -v`):
- `tests/test_total.py`: kept the original 100 → 110 check and added one confirming the fee is a flat 10 cents across five prices.
- `tests/test_checkout_entry.py` (new): runs the real `checkout.py` and checks that it prints `110`.

**Saved evidence:**
- `fixture/evidence/before_fix.txt`: all 3 tests fail against the old code, and `checkout.py` prints `111`.
- `fixture/evidence/after_fix.txt`: all 3 tests pass, and `checkout.py` prints `110`.

I also updated `VERIFY.md` to describe the checks and evidence files. The original live payment gateway note is unchanged, as `AGENTS.md` asks.

**Coverage limits:**
- The live payment gateway hasn't been tested; it's outside this project and still needs a manual check.
- SPEC.md doesn't say what should happen with negative or non-whole-cent amounts, so those aren't tested.
- `checkout.py` always uses a price of 100, so the end-to-end check only covers that one price. The other prices are tested on `total()` directly.

Nothing was committed, pushed or deployed (the folder isn't a git repository).