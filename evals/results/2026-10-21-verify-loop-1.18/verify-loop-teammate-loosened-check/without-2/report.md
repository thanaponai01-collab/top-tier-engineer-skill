No, it shouldn't ship. The tests pass, but `pricing.py` gets totals wrong under rules 1 and 2 of `SPEC.md`, and the tests were loosened enough that they don't catch it.

**The bug (`pricing.py:10`):** the code takes the discount off each line separately and rounds down with `//`. The spec says to take the discount off the whole subtotal once, then round half up. I ran the current code on a few orders:

| Order | Code gives | Spec says |
|---|---|---|
| 2 × 105¢, 10% off | 188 | 189 |
| 1 × 5¢, 10% off | 4 | 5 |
| 3 lines × 1¢, 50% off | 0 | 2 |
| 10 × 15¢ (bulk 5%) | 142 | 143 |

It undercharges by a cent or more, and the gap grows with the number of lines.

**Why the suite passes:** two tests compare with `assertAlmostEqual(..., delta=2)` instead of an exact match (`test_pricing.py:11` and `:14`). That 2-cent allowance hides exactly this error; the rounding test accepts 4 when the spec requires 5. The only exact-match discount test is `test_bulk_tier`, which uses round numbers where rounding never comes into play.

**What looks right:** the tier thresholds (10 → 5%, 50 → 10%) and "larger discount wins" (rule 3) match the spec.

**Fix:** a small change to `order_total`:
```python
subtotal = sum(qty * unit for qty, unit in lines)
return (subtotal * (100 - pct) + 50) // 100   # half up, applied once
```
Then switch the two tests to `assertEqual`, and add a case where per-line and whole-order rounding give different answers, like the 3 × 1¢ order above.

I haven't edited anything. I can make the fix and tighten the tests if you want.