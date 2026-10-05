The 10-cent fee is in. `python -m unittest discover tests` now passes (3 tests), and `python checkout.py` prints `110`. I ran both. Nothing was committed, pushed or deployed.

**Change**
- `app.py`: added `FEE_CENTS = 10`, and `total(cents)` now returns `cents + FEE_CENTS`.
- `checkout.py` needed no change.

**Checks**, all expectations taken from SPEC.md (fixed fee of 10 cents):
- `tests/test_total.py` has the existing `total(100) == 110` check. I added a check that the fee is fixed, not proportional (0 gives 10, 1000 gives 1010).
- `tests/test_checkout_entry.py` is new. It runs `checkout.py` as a subprocess and asserts the output is `110`, so it goes through the real entry point.

**Evidence**, kept in `fixture/evidence/`:
- `before-fix.txt`: before the fix, all 3 tests failed (`100 != 110`, `0 != 10`, entry point printed `100`), exit 1.
- `after-fix.txt`: after the fix, all 3 pass, exit 0.
- `VERIFY.md` now lists the run command and a claim-to-test table, and I left the live-gateway blind-spot note as it was.

**Coverage limits**
- The live payment gateway is not covered. It is outside this project and stays a manual check.
- The entry point only exercises the hard-coded price of 100. `checkout.py` takes no input, so other prices are only checked through `total()`.
- SPEC.md doesn't define negative or non-integer prices, so I didn't test or guard them. Amounts are assumed to be integer cents, per AGENTS.md.