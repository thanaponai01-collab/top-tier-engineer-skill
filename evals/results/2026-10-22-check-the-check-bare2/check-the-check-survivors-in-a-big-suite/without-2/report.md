The worst one: **a change to `split_payment` that drops or misplaces the leftover cents would pass every test.**

Every split the tests check divides evenly: 9000 by 3, 4321 by 1, and 12000 by 4. So `extra` is always 0. The `base + 1` path still runs, which is why coverage looks complete, but nothing ever checks what it produces. I made these changes to a copy of `billing.py` and ran the full suite against each one:

| Change made to a copy of `split_payment` | Result | What actually happens |
|---|---|---|
| `return [base] * ways` | **all 29 pass** | Splitting 100 cents across 3 cards charges 33+33+33 = 99, so a cent is lost. This breaks SPEC rule 6 ("always add up to the total"). |
| Give the extra cents to the *last* cards instead of the first | **all 29 pass** | Breaks SPEC rule 6 ("the first parts carry the extra cents"). |

`test_parts_add_up` was written to catch the first bug. It can't, because 12000 divides evenly by 4.

**Second gap: the 20-seat discount threshold isn't pinned.** The only test in that tier uses 25 seats (and another uses 49). I changed the tier from `(20, 10)` to `(25, 10)` and all 29 tests still passed. So customers with 20–24 seats could lose their 10% discount and drop to 5% without the gate noticing. Seat counts 19 and 20 are never tested. The 10- and 50-seat boundaries are tested on both sides.

As a control, I also broke `apply_credit` (`used = credit`). The suite caught it, so the gate does work where it has a test that can tell the difference.

**Fix:** add these tests:
- `split_payment(100, 3) == [34, 33, 33]`
- `split_payment(10, 4) == [3, 3, 2, 2]`
- a sum check on a total that doesn't divide evenly
- `seat_price("team", 19) == 2755`
- `seat_price("team", 20) == 2610`

**Smaller gaps, untested and not covered by the spec:**
- `prorate(x, 0, 0)` raises `ZeroDivisionError` instead of `ValueError`.
- Negative `credit` isn't rejected, so the amount due goes up.
- Credit that exactly equals the amount is never tested.

I didn't change anything in `fixture/`. The mutated copies were made in a scratch folder and then deleted.