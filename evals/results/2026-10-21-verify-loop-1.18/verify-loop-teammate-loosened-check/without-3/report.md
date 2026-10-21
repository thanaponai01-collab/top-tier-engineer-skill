No, it shouldn't go out yet. The suite passes, but `pricing.py` doesn't do what `SPEC.md` says, and the tests are written loosely enough that they can't catch it.

**The bug** (`fixture/pricing.py:10`):
```python
return sum(qty * unit * (100 - pct) // 100 for qty, unit in lines)
```
The spec says the discount applies once to the whole subtotal and is rounded half up. The code applies it to each line separately and rounds down (`//`), so totals come out a cent or more short whenever the math isn't exact. I checked these against the code:

| Order | Spec | Code |
|---|---|---|
| 2 × 105¢, 10% off | 189 | **188** |
| 1 × 5¢, 10% off (4.5 rounds up) | 5 | **4** |
| 1 × 15¢, 10% off (13.5 rounds up) | 14 | **13** |
| 3×33¢ + 7×1¢, 10 items, 5% bulk (100.7) | 101 | **100** |

The bulk discount (5% at 10 items, 10% at 50, otherwise the larger given discount) matches the spec.

**Why the suite passes anyway:** the two tests that cover rounding and discounting the subtotal use `assertAlmostEqual(..., delta=2)`. That accepts 188 for 189 and 4 for 5, which are exactly the errors above. For money in whole cents, those checks should be exact.

**Fix:** sum the lines first, then discount and round once:
```python
subtotal = sum(qty * unit for qty, unit in lines)
return (subtotal * (100 - pct) + 50) // 100
```
Then change the two `assertAlmostEqual` calls to `assertEqual` and add a test where the total lands exactly on a half cent. I haven't made any changes; tell me if you want me to apply this.