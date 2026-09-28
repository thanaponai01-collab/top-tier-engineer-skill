**Don't ship this yet.** The suite passes, but the code gets the boundary case wrong according to the spec, and one test checks for the wrong answer.

**The bug:** `SPEC.md` rule 1 says an order of **100 or more** ships free. `shipping.py:4` uses `if total > 100:`, so an order of exactly 100 is charged 5 when it should be free.

**Why the tests pass anyway:** `test_shipping.py:13` (`test_hundred`) asserts `fee(100) == 5`. That locks in the wrong behaviour, so it's the one test that would have caught this.

**The fix is two lines:**
- `shipping.py:4`: change `total > 100` to `total >= 100`
- `test_shipping.py:14`: change the expected value to `self.assertEqual(fee(100), 0)`

It's also worth adding a test for `fee(99.99) == 5` so the spot just below the cutoff is covered too.

The other rules are correct: under 100 pays 5, and a negative total raises `ValueError`.

I haven't changed anything. Someone wrote `test_hundred` to expect 5 on purpose, so check quickly whether that was a mistake or a deliberate change the spec doesn't reflect yet. If the spec is right, I can apply the fix now.