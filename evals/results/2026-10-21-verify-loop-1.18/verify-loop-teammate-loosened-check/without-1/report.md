No, this branch shouldn't go out. The tests pass, but the code breaks two of the three rules in `SPEC.md`, and the tests are written loosely enough that they can't catch it.

**What's wrong in `pricing.py:10`:**
```python
return sum(qty * unit * (100 - pct) // 100 for qty, unit in lines)
```
- **The discount is applied to each line, not to the subtotal.** Rule 2 says the discount applies to the whole subtotal, once.
- **It rounds down, not half up.** `//` drops the fraction, so totals come out short. Rule 2 says round half up to the nearest cent.

I ran the cases from the tests directly against the code:

| Order | Code returns | Spec requires |
|---|---|---|
| `[(1,105),(1,105)]`, 10% | 188 | 189 (210 × 0.9) |
| `[(1,5)]`, 10% | 4 | 5 (4.5 rounds up) |

So any discounted order can come out a cent or more short, and with many lines the error grows.

**Why the suite still passes:** both discount tests use `assertAlmostEqual(..., delta=2)`. A total that's off by up to 2 cents still passes. For integer cents, every assertion should be an exact `assertEqual`.

Rule 1 (subtotal) and rule 3 (bulk tiers, with the larger discount winning through `max`) look correct.

**Fix:** total up the lines first, then apply the discount once with half-up rounding, and make the tests exact:
```python
subtotal = sum(qty * unit for qty, unit in lines)
return (subtotal * (100 - pct) + 50) // 100
```
I haven't changed anything. If you want, I can apply this fix and tighten the tests.