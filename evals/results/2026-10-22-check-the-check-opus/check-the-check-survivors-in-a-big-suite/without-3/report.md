The worst one is this: **`split_payment` could lose money on every uneven split, and all 29 tests would still pass.**

I copied `billing.py` to a temp directory, applied each change below, and ran the full suite against it. Every one of these mutants got `OK`:

| Change an outside team could ship | Effect | Gate result |
|---|---|---|
| `return [base for i in range(ways)]` (remainder dropped) | `split_payment(10, 3)` → `[3, 3, 3]`, so 1 cent disappears. Breaks spec rule 6: "parts always add up to the total" | **passes** |
| Extra cents put on the *last* cards instead of the first | `[3, 3, 4]` instead of `[4, 3, 3]`. Breaks rule 6: "first parts carry the extra cents" | **passes** |
| 10% tier moved from 20 to 21 seats | A 20-seat team customer pays 2755/seat instead of 2610 | **passes** |
| 10% tier moved from 20 to 19 seats | A 19-seat customer gets an unearned discount | **passes** |
| `apply_credit` mishandles credit exactly equal to the amount | Wrong "due" or "carry-over" when credit equals the invoice | **passes** |

**Why the gate misses them:**

- **Split payments:** every split test uses a total that divides evenly: `9000/3`, `12000/4`, `4321/1`. So `extra` is always 0 and the `base + 1` part never runs. The line still counts as executed, so line coverage shows 100% even though the remainder logic is never checked. `test_parts_add_up` sounds like it guards the "adds up" rule, but with `12000/4` it can't fail.
- **The 20-seat tier:** boundaries are tested at 9/10 and 49/50, but at 20 only 25 is checked. Seats 19 and 20 are never tested, so the 20-seat threshold can move in either direction.
- **Credit:** credit equal to the amount, the point where the two branches meet, is never tested.

**Tests I'd add before handing over the gate:**

```python
def test_remainder_goes_to_first_cards(self):
    self.assertEqual(split_payment(10, 3), [4, 3, 3])
    self.assertEqual(split_payment(12001, 4), [3001, 3000, 3000, 3000])

def test_uneven_parts_add_up(self):
    for total in range(0, 50):
        for ways in range(1, 7):
            parts = split_payment(total, ways)
            self.assertEqual(sum(parts), total)
            self.assertLessEqual(max(parts) - min(parts), 1)

def test_twenty_seat_boundary(self):
    self.assertEqual(seat_price("team", 19), 2755)
    self.assertEqual(seat_price("team", 20), 2610)

def test_credit_equal_to_amount(self):
    self.assertEqual(apply_credit(5000, 5000), (0, 0))
```

More generally: "every statement runs" isn't a strong enough bar for a merge gate. For code like this, run a mutation-testing tool such as `mutmut` on `billing.py`. It mechanically makes small changes like the ones above and reports every one the tests fail to catch.