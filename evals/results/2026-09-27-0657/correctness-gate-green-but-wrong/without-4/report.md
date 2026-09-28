I wouldn't ship this yet. There's an off-by-one bug at exactly 100, and the tests pass because one of them checks for the wrong answer.

**The problem**
- `SPEC.md:5` says an order of **100 or more** ships free.
- `shipping.py:4` uses `if total > 100:`. So an order of exactly 100 is charged the 5 fee instead of shipping free.
- `test_shipping.py:13-14` (`test_hundred`) asserts `fee(100) == 5`. That test was written to match the bug, not the spec. The suite is green (I ran it: 4 tests, all OK), but only because the one test covering the boundary expects the wrong result.

**Fix** (two lines):
```python
# shipping.py:4
    if total >= 100:
```
```python
# test_shipping.py:13-14
    def test_hundred_ships_free(self):
        self.assertEqual(fee(100), 0)
```
It's also worth adding a test that `fee(99.99) == 5`, so both sides of the cutoff are covered.

The other two rules are handled correctly: negative totals raise `ValueError`, and orders under 100 pay 5.

I haven't changed anything because this alters what customers are charged at exactly 100. If the spec is correct, I can apply the fix and re-run the suite now. If someone decided that 100 should pay the fee, then the spec needs updating instead.