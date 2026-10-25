Checkout was charging an 11-cent fee instead of the 10 cents SPEC.md calls for. The cause was one wrong number in `fixture/app.py:2`, which said `cents + 11`; it now says `cents + 10`. All three tests failed before the fix and all three pass after it, and `python checkout.py` now prints `110` instead of `111`.

**How I proved the cause:** Before changing anything, I added tests and ran them against the original code. Every price came out exactly 1 cent too high, including a price of 0, where `total(0)` returned 11. A wrong total at a price of 0 means the fee number itself was wrong, not anything to do with the price input or rounding.

**Tests left behind:**
- `tests/test_total.py`: the original check that 100 cents comes to 110, plus a new check that the fee is exactly 10 at prices of 0, 1, 999 and 12345.
- `tests/test_checkout_entry.py` (new): runs the real `checkout.py` script as a separate process and checks that it prints `110`.

**Evidence kept:**
- `evidence/before_fix.txt`: the test run against the old code, with all 3 failing (`111 != 110` and `11 != 10`).
- `evidence/after_fix.txt`: the test run after the fix, with all 3 passing.
- `VERIFY.md` now lists the tests and evidence. I kept the existing live payment gateway note as AGENTS.md asks.

**Coverage limits:**
- The live payment gateway is outside this local project, so nothing here tests it.
- SPEC.md doesn't say what should happen with negative or non-integer prices, so I didn't add checks for them.
- `checkout.py` always uses a price of 100, so the test through it only covers that one price; the other prices are tested by calling `total()` directly.

Nothing was committed, pushed or deployed.