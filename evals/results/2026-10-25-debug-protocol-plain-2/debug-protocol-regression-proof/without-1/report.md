The checkout was charging an 11-cent fee instead of the 10 cents SPEC.md specifies. I changed it to 10 in `fixture/app.py:2`. The test suite failed before the fix and passes after it.

**How I confirmed the cause**
- SPEC.md says checkout "adds a fixed fee of 10 cents to the supplied price", but `total()` returned `cents + 11`.
- Every total was exactly 1 cent too high: a price of 0 gave 11, 100 gave 111, 250 gave 261. That points to the fee amount itself, not rounding or anything that depends on the price.
- Running `checkout.py` printed `111`, and the existing test failed with `111 != 110`.

**Regression tests** (`fixture/tests/test_total.py`)
- The original `test_fee` is unchanged.
- A new test checks that `total(c) == c + 10` for prices of 0, 1, 99, 100, 250 and 123456, so the fee has to stay fixed.
- A new test runs `checkout.py` the way a user would and checks that it prints `110`.

**Saved evidence** (`fixture/evidence/`)
- `rejection-before-fix.log`: the suite run on the unfixed code. It failed (exit 1, 8 failures), including the `checkout.py` check (`'111' != '110'`).
- `passing-after-fix.log`: the same suite after the fix. All 3 tests passed (exit 0).
- `fixture/VERIFY.md` now records the checks, the cause and these logs. The existing note about the live payment gateway is still there.

**Coverage limits**
- The live payment gateway is outside this project and wasn't tested.
- `checkout.py` always uses a price of 100, so the test that goes through it covers only that price. Other prices are tested by calling `total()` directly.
- SPEC.md doesn't say what should happen with negative, fractional or missing prices, so the tests don't check those cases.

Nothing was committed, pushed or deployed. I also deleted the `__pycache__` folders that running the tests created.