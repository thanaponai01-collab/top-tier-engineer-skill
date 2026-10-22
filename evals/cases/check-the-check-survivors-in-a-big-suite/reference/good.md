# What could get past test_billing.py

I planted every one-line bug I could generate in billing.py (53 of them), one at a time in a scratch
copy, and ran the 29 tests against each. Four survived; two are real gaps.

1. **Uneven splits are never tested.** `split_payment` is only tested on totals that divide evenly
   (9000/3, 12000/4, one card). Changing `base + 1` to `base - 1` still passes, so splitting 1000
   three ways could return [332, 333, 333], which adds up to 998 against SPEC.md 6. Add
   `split_payment(1000, 3) == [334, 333, 333]`.
2. **The 20-seat tier is never tested at exactly 20.** The tests hit 10 and 50 exactly, but the
   10% tier only at 25 and 49. Moving the tier in `VOLUME_TIERS` from 20 to 21 seats still passes.
   Add `seat_price("team", 20) == 2610` and `seat_price("team", 19) == 2755`.

The other survivor, `days_late <= GRACE_DAYS` changed to `<`, changes nothing visible: on day 7 the
interest is 0 either way. Every other mutant (prices, tiers 10 and 50, proration rounding, credit,
grace period, interest) turned the suite red.
