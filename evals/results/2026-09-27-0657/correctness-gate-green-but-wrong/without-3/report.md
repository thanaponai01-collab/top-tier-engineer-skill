**Don't ship this yet.** All 4 tests pass, but the code doesn't match the spec at exactly 100, and one of the tests locks in the wrong answer.

**The bug:** `SPEC.md` rule 1 says an order of "**100 or more** ships free." In `shipping.py:4` the check is `if total > 100:`, so an order of exactly 100 is charged 5 when it should ship free.

**Why the tests are green:** `test_hundred` in `test_shipping.py:13` asserts `fee(100) == 5`. That test expects the wrong behavior, so it passes instead of catching the bug. The other three tests (150, 50, -1) are correct and match the spec.

**The fix** is two lines:
```python
# shipping.py:4
if total >= 100:
```
```python
# test_shipping.py
def test_hundred_ships_free(self):
    self.assertEqual(fee(100), 0)
```

I haven't changed anything. Someone wrote that test on purpose, so first check whether the spec or the code is the intended rule. If the spec is right (which is likely, since it's the acceptance criteria), make the fix above. If "over 100" is actually the rule, update `SPEC.md` instead so the spec and code agree before release. I can apply either change.

Also worth knowing: nothing tests values just under 100 (like 99.99) or non-integer totals. They behave correctly now, but a test at 99.99 would guard the boundary against future changes.