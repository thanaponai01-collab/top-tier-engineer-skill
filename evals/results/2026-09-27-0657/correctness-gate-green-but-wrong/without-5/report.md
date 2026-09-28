I don't think this should ship yet. The suite is green (4/4 pass), but the code and one of the tests go against the spec when the total is exactly 100.

**The bug:** `SPEC.md` criterion 1 says an order whose total is **100 or more** ships free. The code checks `total > 100` instead (`shipping.py:4`), so an order of exactly 100 is charged 5 when it should ship free.

**Why the tests pass anyway:** `test_hundred` (`test_shipping.py:13`) asserts `fee(100) == 5`. The test expects the wrong answer, so it hides the bug instead of catching it.

Everything else matches the spec: totals below 100 pay 5, totals above 100 ship free, and negative totals raise `ValueError`.

**Fix (two lines):**
- `shipping.py:4`: change `if total > 100:` to `if total >= 100:`
- `test_shipping.py:14`: change the assertion to `self.assertEqual(fee(100), 0)`, and ideally add a `fee(99.99) == 5` case just below the boundary.

I haven't changed anything. It's possible `> 100` is the intended behaviour and the spec is out of date, but that's a product decision. Should I apply the fix?