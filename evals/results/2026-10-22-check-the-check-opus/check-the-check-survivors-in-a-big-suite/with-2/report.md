Yes, two kinds of billing bug would get past this gate. The suite is green (29 tests), every statement runs, and I planted 53 one-line bugs in `billing.py`: 49 made it fail and 4 didn't. Two of those 4 are real gaps; the other two don't change any result.

**Gaps (a broken change would still merge):**

1. **The 20-seat discount boundary is never tested.** I changed the 10%-off tier from "20 or more seats" to "21 or more" and every test still passed. The tests check 9, 10, 25, 49 and 50 seats, but not 20. Under the spec (rule 2), `seat_price("team", 20)` should be **2610**; the broken version charges **2755** and the gate doesn't notice. Test to add: `seat_price("team", 20) == 2610`. It would also help to check 19 seats (should be 2755) so the boundary is pinned from both sides.

2. **Splitting a total that doesn't divide evenly is never tested.** All the split tests use exact divisions (9000/3, 12000/4, one card). I made the extra cent go the wrong way (`base - 1`, or `base + 2`) and the gate stayed green. Under rule 6, `split_payment(100, 3)` should be **[34, 33, 33]**. The broken versions give [32, 33, 33], which adds up to 98, or [35, 33, 33], which adds up to 101. Either way the parts don't add up to the total and the customer is charged the wrong amount. The same gap would let someone put the extra cents on the last cards instead of the first. Test to add: `split_payment(100, 3) == [34, 33, 33]`.

**The other two survivors change nothing:**
- Changing the grace check from `days_late <= 7` to `< 7` gives the same answer. On day 7 the formula is `amount * 0 // 1000 = 0`, so it's 0 either way, and no input produces a different result.
- The second split survivor is the same gap as #2.

**What the gate does catch:** every other planted bug failed it. That covers the plan prices, unknown plans and zero seats, the 10- and 50-seat tiers, rounding down discounted prices, the annual 10-for-12 rule, proration (including rounding half up and the range checks), credit in both directions and carried over, rejecting zero cards, and late interest after the grace period, including rounding down.

So line coverage and exact amounts weren't enough here: the 20-seat boundary and uneven splits are both unguarded. Add those two tests before the outside team relies on this gate. I haven't changed any files; the only thing I created was a `__pycache__` from a quick spot-check of the values above, and I deleted it. If you want me to write the tests and show each one failing against the planted bug, the verify-loop skill does that.