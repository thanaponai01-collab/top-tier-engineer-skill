**Answer: no, the gate is not strong enough to let an outside team change billing.py unchecked.** The helper's verdict is `weak`: 49 of 53 planted one-line bugs were caught, and 4 survived. Two of the survivors are real gaps and one changes nothing observable. The 29 tests all ran, and no file was loaded or collected without running.

**Gaps:**

1. **Split payments with a remainder are never tested.** Every split test uses a total that divides evenly (9000/3, 4321/1, 12000/4). A bug in the extra-cent logic goes unnoticed. Changing `base + 1` to `base - 1` for the first parts survives. With the mutant, `split_payment(10, 3)` returns `[2, 3, 3]`, which sums to 8 instead of 10. The spec (rule 6) says the parts must add up to the total, and the original returns `[4, 3, 3]`. The test to add: `split_payment(10, 3) == [4, 3, 3]` and `sum(...) == total` for an uneven total. A `base + 2` mutant also survives, producing `[5, 3, 3]`, which sums to 11.

2. **The 20-seat volume tier is never tested.** The tests cover 10, 25, 49 and 50 seats, but not the boundary at 20. Changing the threshold from 20 to 21 survives. For `seat_price("team", 20)`, the original returns 2610 (10% off, per rule 2) and the mutant returns 2755 (5% off). The test to add: `seat_price("team", 20) == 2610`.

**Survivor with no observable change:**

- `late_interest` at `days_late == GRACE_DAYS`: changing `<=` to `<` survives, but at exactly 7 days the formula gives `amount * 0 // 1000 = 0` either way. The mutant is equivalent for every input the spec allows, so this is not a gap.

**What held:** the helper caught the other 49 planted bugs, so those rules are covered by the current tests. Examples include the 10/50 tier edges, the grace-period and rounding behaviour in the cases the tests reach, and the ValueError paths. I did not list each caught mutant, so I can't name every covered rule beyond that.

**Evidence:** I ran `python -m unittest test_billing` from the repo root in a scratch copy, with `--product billing.py`. No base ref was given, so the new-test check did not apply. I confirmed the original outputs directly: `seat_price("team", 20)` = 2610, `split_payment(10, 3)` = `[4, 3, 3]`, `late_interest(50000, 7)` = 0. There is no CI file in `fixture/`, so I used the test command as the check. I changed nothing in the repo.