I fixed the checkout fee: it was 11 cents but SPEC.md says it should be 10. All tests pass now, and `python checkout.py` prints `110` instead of `111`.

**Cause:** `fixture/app.py:2` added a hard-coded `11` instead of `10`. Every price I tried came out exactly 1 cent too high, including a price of 0 (which gave 11). So the fee number itself was wrong; it isn't a rounding problem or anything that depends on the price.

**Fix:** I changed one line in `app.py`, from `cents + 11` to `cents + 10`.

**Regression tests:** I added `tests/test_checkout_entry.py`:
- **Fee test:** checks that the total is the price plus 10 for prices of 0, 1, 100 and 12345 cents, based on SPEC.md's "fixed fee of 10 cents".
- **Checkout test:** runs `checkout.py` itself as a separate process and checks that it prints `110`.

The existing test in `tests/test_total.py` is unchanged.

**Saved test runs** (in `fixture/evidence/`):
- `before-fix.txt`: run against the old code. The 6 assertions (1 for the old test, 4 for the fee test's prices, 1 for the checkout test) all failed, with exit code 1.
- `after-fix.txt`: run after the fix. All 3 tests pass, with exit code 0.

I also updated `VERIFY.md` with how to run the tests, the cause, and where the saved runs are. The existing note about the live payment gateway is still there.

**What the tests don't cover:**
- The live payment gateway is outside this project and still has to be checked manually.
- Only whole-cent amounts are tested. Negative, fractional and very large amounts aren't defined in SPEC.md, so there are no tests for them.
- `checkout.py` always uses a price of 100 and takes no input, so the checkout test only checks that one price.

Nothing was committed, pushed or deployed. The folder isn't a git repository.