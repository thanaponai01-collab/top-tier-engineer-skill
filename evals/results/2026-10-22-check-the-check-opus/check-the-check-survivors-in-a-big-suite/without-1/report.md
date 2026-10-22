The clearest one: **`split_payment` can quietly lose money and the gate will still pass.**

If `billing.py:47` is changed from

```python
return [base + 1 if i < extra else base for i in range(ways)]
```

to

```python
return [base] * ways
```

all 29 tests still pass. I ran it. But `split_payment(100, 3)` then returns `[33, 33, 33]`, which adds up to 99, so a cent is lost on every uneven split. That breaks SPEC rule 6, which says "the parts always add up to the total."

**Why the gate misses it:** every split test uses a total that divides evenly (9000/3, 4321/1, 12000/4). So the code that hands out the leftover cents runs, which is why coverage shows every statement executed, but it never has a leftover to hand out. Even `test_parts_add_up` checks an even split. Moving the extra cents to the *last* cards instead of the first, which the spec also forbids, would get through for the same reason.

**A second gap I confirmed by running it:** the 20-seat discount boundary is never tested. The tests check 9, 10, 25, 49 and 50 seats, but not 19 or 20. Changing the tier from `(20, 10)` to `(25, 10)` still passes all tests, even though customers with 20–24 seats would then be overcharged (5% off instead of 10%).

**Tests to add before handing it over:**
- `split_payment(100, 3) == [34, 33, 33]`, plus a sum check on an uneven total.
- `seat_price("team", 19) == 2755` and `seat_price("team", 20) == 2610`.

I tested these changes on a copy of `billing.py` in `../mut/`. Your `fixture/` files were not changed.