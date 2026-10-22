Several. I made each of the following one-line changes to a copy of `billing.py` and ran the full suite against it. **All 29 tests still passed every time**, even though each change breaks a rule in `SPEC.md`:

| Change an outside team could ship | Spec rule broken | Real-world effect |
|---|---|---|
| `monthly_amount` returns `PLANS[plan] * seats`, skipping `seat_price` | §2/§3 | **No volume discount on any bill.** A 50-seat team customer is charged 145,000 instead of 123,250 per month. |
| `split_payment` returns `[base] * ways` | §6 | **The leftover cents vanish.** Splitting 100 across 3 cards charges 99. |
| `split_payment` puts all the leftover cents on the first card (`[base + extra] + [base] * (ways-1)`) | §6 | Parts can differ by more than 1 cent (10 across 4 cards gives 4,2,2,2). |
| Change the 10% tier from `(20, 10)` to `(25, 10)` | §2 | Customers with 20–24 seats lose 5 percentage points of discount. |

**Why the gate misses them:**
- **The discount is only tested on `seat_price` directly.** Every test of `monthly_amount`, `annual_amount` and `invoice` uses 2 or 3 seats, where no discount applies. Nothing checks that the discount actually reaches the amount billed.
- **Every split test divides evenly.** `test_parts_add_up` uses 12000 ÷ 4, so the remainder logic is never exercised. The fact that `extra` is always 0 also explains why every statement runs while the "first parts carry the extra cents" rule goes unchecked.
- **The tier tests sit at 9/10, 25, 49 and 50.** Nothing tests 19 or 20, so the 20-seat threshold can move anywhere from 11 to 25 without a test failing.

There are smaller gaps too: no test combines annual billing with credit, and none uses an annual invoice with enough seats to get a discount.

**Tests to add before handing off:**
- `monthly_amount("team", 50) == 123250`
- `split_payment(100, 3) == [34, 33, 33]`
- `split_payment(10, 4) == [3, 3, 2, 2]`
- `seat_price("team", 19) == 2755` and `seat_price("team", 20) == 2610`
- One annual invoice with a discount and credit, e.g. `invoice("team", 20, annual=True, credit=1000) == (521000, 0)`

Full statement coverage and exact amounts only show that the tests ran each line with one kind of input. Here those inputs were chosen so the discount and the remainder never come into play.