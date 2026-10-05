The checkout fee is in. `total()` now returns the price plus 10 cents, and `python checkout.py` prints `110`. `run --strict` and `status` both ended at `VERIFY-STATE: green`. I did not commit, push or deploy; the folder isn't a git repo anyway.

**What changed (all in `fixture/`)**
- **`app.py`:** added `FEE_CENTS = 10`, and `total()` returns `cents + FEE_CENTS`. `checkout.py` already called `total()`, so I left it alone.
- **`tests/test_checkout_entry.py`:** new test that runs `checkout.py` as a subprocess and expects `110`. This is the check through the real entry point.
- **`VERIFY.md`:** added a "Checkout fee" section that takes its expectation from `SPEC.md`. I kept the live-gateway blind-spot note and added one more.
- **`BUILD.md`:** new, records the proof line and the deferred items.

**Rejection evidence**
- Before the fix, both tests failed. The existing `test_total.py` gave `AssertionError: 100 != 110 : expected total 110`. The new entry-point test failed too. I only saw the first failure message in the output; the entry-point failure is counted in `FAILED (failures=2)`.
- After the fix, `python -m unittest discover tests` passes, and so does the strict run.
- The failing and passing runs are kept in `.verify-state.json`, which `verify.py` writes in `fixture/`.

**Coverage limits**
- **Live gateway:** the live payment gateway isn't exercised. It is marked MANUAL in `VERIFY.md`.
- **Amounts:** only the 100-cent price is checked through `checkout.py`, because it hardcodes 100. I added no tests for other amounts.
- **Challenge run:** I did not run `verify.py challenge`, which tries a deliberate wrong change in scratch copies. The only rejection evidence is the red run before the fix.
- **Scope of green:** strict green covers only the mapped fee claim.

<!-- file written by the agent: fixture/BUILD.md -->
# BUILD

- `python -m unittest discover tests` -> OK; `python checkout.py` -> `110` (SPEC.md: +10 cent fee) | proven | uncommitted (no git repo; user said not to commit)
  - Evidence: red before fix (`100 != 110`, 2 failures), strict green after; receipts in `.verify-state.json`.

## Deferred
- Live payment gateway | outside local project | MANUAL, prove in an environment with the gateway
- Amounts other than 100 via checkout.py | entry point hardcodes 100 | checkout.py accepts input -> add a test
