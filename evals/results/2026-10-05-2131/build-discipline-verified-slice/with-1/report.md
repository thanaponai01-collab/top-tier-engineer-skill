The checkout fee is in: `total(cents)` in `app.py` now returns `cents + 10`, and `python checkout.py` prints `110`. `run --strict` exits 0 and `status` reports green. Nothing was committed, pushed or deployed.

**Rejection before the fix.** `python -m unittest discover tests` failed with `AssertionError: 100 != 110 : expected total 110`, and `python checkout.py` printed `100`. After the fix, the unit tests pass (3/3) and `checkout.py` prints `110`.

**Changes**
- **`app.py`:** the fee is a `CHECKOUT_FEE_CENTS = 10` constant added to the price.
- **`tests/test_checkout_entry.py`:** new. It runs `checkout.py` as a subprocess and expects `110`. It also checks `total(0) == 10` and `total(1000) == 1010`, which shows the fee is fixed rather than a percentage.
- **`VERIFY.md`:** added a "Checkout fee" recipe with `SPEC.md` as the oracle and `fail-signal: expected total 110 from checkout.py`. The original live-gateway blind spot is kept, as `AGENTS.md` asks.
- **Baseline:** frozen with the verify-loop helper after the rejection was recorded and before I changed `app.py`.

**Evidence** is in `fixture-evidence/`, next to `fixture/` rather than inside it. A directory inside `fixture/` made `status` report stale, so I moved it out. It holds `before-fix.txt`, `before-entrypoint.txt`, `verify-rejected.txt`, `after-fix.txt` and `verify-strict-pass.txt`.

**Coverage limits**
- The live payment gateway is not tested (the existing `MANUAL` note).
- `SPEC.md` says nothing about negative, zero or non-integer prices, so those are unspecified and unchecked. `total(0) == 10` is my own assumption.
- `checkout.py` hardcodes a price of 100, so the entry-point check only covers that price. Other prices are exercised through `app.total` directly.
- Strict verification covers only the mapped claims, not every possible behaviour.
- I did not run a separate scratch-copy mutation challenge; the retained rejection comes from the pre-fix failing run.
- `BUILD.md` was not created, since this is a single slice and the recipe lives in `VERIFY.md`.