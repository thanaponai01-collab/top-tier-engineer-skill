**Don't ship this yet. The code contradicts the spec at exactly 100, and the tests are green because one of them checks for the wrong answer.**

- `SPEC.md` criterion 1 says an order of **100 or more** ships free.
- `shipping.py:4` uses `if total > 100:`, so an order of exactly 100 pays 5.
- `test_shipping.py`'s `test_hundred` asserts `fee(100) == 5`. That test matches the bug, not the spec.

I ran the suite and all 4 tests pass. That's why green doesn't mean correct here: every order totalling exactly 100 would be charged 5 when it should ship free.

**Fix (two lines):**
- `shipping.py`: `if total > 100:` → `if total >= 100:`
- `test_shipping.py`: `test_hundred` should assert `fee(100) == 0`

I'd also add a test that `fee(99.99) == 5`, so the boundary is checked from both sides.

The other two criteria are implemented and tested correctly: under 100 pays 5, and a negative total raises `ValueError`. One small gap: a total of 0 has no test. It returns 5, which matches the spec as written.

Do you want me to make the change? Also check whether anyone decided on purpose that exactly 100 should pay. If so, the spec is what needs changing, not the code.