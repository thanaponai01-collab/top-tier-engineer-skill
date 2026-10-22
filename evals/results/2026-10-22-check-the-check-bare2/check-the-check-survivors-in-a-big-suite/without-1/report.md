The gate would let all five of the bugs below ship. I tested each one: I changed a copy of `billing.py` in a temp directory and ran the full 29-test suite, and it passed every time. Your `fixture/` files were not modified.

| # | Bug an outside team could ship | Spec rule broken | Why no test catches it |
|---|---|---|---|
| 1 | **`monthly_amount` drops the volume discount** (e.g. `PLANS[plan] * seats`) | §2/§3 | Every test of `monthly_amount`, `annual_amount` and `invoice` uses 2–3 seats. The discount is only checked on `seat_price` by itself, never on an amount a customer is actually billed. |
| 2 | **The 20-seat tier starts at 21** (or any number up to 25) | §2 | The 10 and 50 boundaries are tested on both sides (9/10, 49/50). Tier 2 is only tested at 25 and 49, so seats 19 and 20 are never checked. |
| 3 | **`split_payment` puts the extra cents on the *last* cards** | §6 "first parts carry the extra cents" | The only uneven split (12000/4) is checked with `sum(...)`, which doesn't care about order. |
| 4 | **`split_payment` puts the whole remainder on card 1** (e.g. 10/3 → `[5,3,2]`… or `[3+extra, …]`) | §6 "differ by at most one cent" | Same reason: only the sum is checked, never the individual parts. |
| 5 | **Annual invoices ignore account credit** | §5 | Credit is only tested on monthly invoices, and the annual invoice test uses `credit=0`. |

Bug #1 is the serious one. A customer with 50 seats on business would be overcharged 15% on every invoice, while the gate passes and the coverage report shows 100%. The tests run every statement, but they never compare a billed amount where the discount applies.

These tests would close the gaps:
- `monthly_amount("team", 10) == 27550`, plus annual and `invoice` cases with ≥10 seats
- `seat_price("team", 19) == 2755` and `seat_price("team", 20) == 2610`
- `split_payment(10, 3) == [4, 3, 3]`, and change `test_parts_add_up` to check the exact list (`[3000]*4`), not just the sum
- `invoice("starter", 2, annual=True, credit=500) == (17500, 0)`

Smaller gaps I noticed but didn't test:
- `prorate(x, 0, 0)` raises `ZeroDivisionError`, and the spec doesn't say what should happen.
- Credit exactly equal to the amount is never tested.
- Nothing checks inputs like negative amounts or negative days late.

Running a mutation-testing tool such as `mutmut` on `billing.py` before letting the outside team in would find any further gaps like these automatically.