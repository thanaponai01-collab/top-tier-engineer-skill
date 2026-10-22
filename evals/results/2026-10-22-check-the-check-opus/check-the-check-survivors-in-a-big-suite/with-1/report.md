**No, the gate isn't safe yet.** I planted 53 one-line bugs in `billing.py`. The 29 tests caught 49 of them. Three of the bugs that got through break a rule in `SPEC.md` and could ship behind this gate. The fourth changes nothing a customer would see.

**Bugs it would not catch:**

- **The 10% discount could start at 21 seats instead of 20 (spec rule 2).** I changed the tier minimum from 20 to 21 and all 29 tests passed. The tests check 9, 10, 25, 49 and 50 seats but never exactly 20. With that bug, 20 team seats would bill at 2755 a seat instead of 2610. The missing test: `seat_price("team", 20) == 2610`.
- **Card splits could give the leftover cents wrong (spec rule 6).** I changed `base + 1` to `base - 1`, and separately to `base + 2`. Both versions passed. Every split in the tests divides exactly (9000 by 3, 12000 by 4), so the code that hands out leftover cents never actually runs. With these bugs, `split_payment(10, 3)` would return `[2, 3, 3]` (adds up to 8) or `[5, 3, 3]` (adds up to 11) instead of `[4, 3, 3]`. Customers' cards would be charged more or less than the invoice. The `test_parts_add_up` test looks like it guards this but doesn't, because 12000 splits evenly 4 ways. The missing test: `split_payment(10, 3) == [4, 3, 3]`, which also checks that the parts add to 10.

**The bug that changes nothing:** changing the grace check from `<= 7` to `< 7`. On day 7 the interest formula multiplies by zero days past grace, so the result is 0 either way.

**What held:** breaking any of these got at least one test to fail: the list prices, the 5% and 15% discount boundaries, rounding down on discounts, the 10-of-12 annual rule, proration rounding and its range check, credit carry-over, rejecting zero cards, and late interest amounts and rounding. Running every line and checking exact amounts didn't cover the gaps above, because the inputs never land on the 20-seat boundary or on a split with leftover cents.

**Limit of this check:** it only plants one-line bugs. A larger rewrite could still get past these tests, so this result is a minimum set of gaps, not a full list.

The command I ran was `python -m unittest test_billing`, against a scratch copy, and the repo is unchanged. I haven't added the missing tests. If you want them written and shown failing, then passing, that's the verify-loop skill.