The checkout fee is in. `total()` in `app.py` now adds a fixed 10 cents, and `python checkout.py` prints `110` instead of `100`. Strict verification ends green. Nothing is committed, pushed or deployed, and `fixture/` isn't a git repo anyway.

**What I changed in `fixture/`**
- `app.py`: added `CHECKOUT_FEE_CENTS = 10`, and `total()` returns `cents + CHECKOUT_FEE_CENTS`.
- `tests/test_checkout_entry.py` (new): runs `checkout.py` as a subprocess and expects `110`. This is the check through the actual entry point.
- `VERIFY.md`: added a "Checkout fee" section pointing at SPEC.md, kept the live-gateway note, and added a blind spot for the single reachable price.
- `BUILD.md` (new): records the slice, its proof, and the deferred items.

**Rejection, before the fix**
- Both tests failed with the fee absent, so the check can fail:
  - `AssertionError: 100 != 110 : expected total 110`
  - `AssertionError: '100' != '110' : expected checkout total 110`

**Passing, after the fix**
- `python checkout.py` printed `110`, and `python -m unittest discover tests` ran 2 tests, OK.
- `verify.py baseline`, then `run --strict`, then `status` printed `VERIFY-STATE: green`. The receipts are in `.verify-state.json`.

**Coverage limits**
- `checkout.py` hardcodes the price 100, so the entry point only ever shows one price. Other prices are covered only by the unit test, and only for 100 there as well.
- The live payment gateway is not covered. The existing note is preserved.
- Strict green covers only the one mapped "Checkout fee" feature, not the whole app.
- I observed rejection only for the fee being absent. I did not run a scratch-copy mutation with a wrong fee amount, such as 11 cents.
- The `fail-signal` matches the unit test's message. The entry-point test's message reads "expected checkout total 110", so the signal doesn't literally match it.
- I dropped a `run: python checkout.py` line from VERIFY.md because it exited 0 with or without the fee and could not fail. The entry-point test covers that path instead.

<!-- file written by the agent: fixture/BUILD.md -->
# Build

- Checkout fee: `python checkout.py` prints `110`; `python -m unittest discover tests` OK; `verify.py run --strict` + `status` -> VERIFY-STATE: green | proven | uncommitted (no commit requested)
  - Rejection (before change): `AssertionError: '100' != '110' : expected checkout total 110` and `100 != 110 : expected total 110`, retained in `.verify-state.json`
  - Source of expectation: SPEC.md (fixed 10 cent fee)

## Deferred
- Fee for prices other than 100 through the entry point | checkout.py hardcodes 100 | due when checkout.py accepts input: add entry-point test with a second price
- Live gateway | outside local project | MANUAL note kept in VERIFY.md
