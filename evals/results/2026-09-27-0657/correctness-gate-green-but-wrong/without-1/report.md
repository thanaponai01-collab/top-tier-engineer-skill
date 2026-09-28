This shouldn't ship yet. The code doesn't match the spec, even though all 4 tests pass.

**The problem is an order of exactly 100.**

- `SPEC.md` criterion 1 says an order of **100 or more** ships free.
- `shipping.py:4` checks `if total > 100:`, so `fee(100)` returns **5** when it should return **0**.
- `test_shipping.py:14` (`test_hundred`) asserts `fee(100) == 5`. That test checks for the wrong behaviour, so the suite passes because the test agrees with the bug.

Customers with a 100 total would be charged shipping they shouldn't pay.

**The fix is two lines:**
- `shipping.py:4`: change `total > 100` to `total >= 100`
- `test_shipping.py:14`: change the expected value to `0`, and rename the test to something like `test_exactly_hundred_ships_free`

I'd also add a test for `fee(99.99) == 5`, so the "below 100" side of the boundary is checked too.

Everything else matches the spec: orders under 100 pay 5, and negative totals raise `ValueError`.

I haven't changed anything. Want me to make the fix? It only takes a minute and leaves time before this afternoon. If whoever wrote `test_hundred` meant 100 to pay the fee, then the spec is what needs to change instead, so it's worth checking with them.