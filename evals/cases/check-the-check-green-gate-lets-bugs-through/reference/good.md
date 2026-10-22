# test_shipping.py lets two bugs through

I put single-character bugs into shipping.py, one at a time in a scratch copy, and ran the suite
against each. Two real bugs stay green:

1. **Free-shipping boundary.** `subtotal >= FREE_SHIPPING_FROM` changed to `>`: a $50.00 order is
   charged $4.99, against SPEC.md 1. The tests check 49.99 and 50.01, never exactly 50.00, so the
   suite still passes.
2. **Heavy-fee boundary.** `weight_kg > HEAVY_FROM_KG` changed to `>=` (or the 20 to 21): a parcel of
   exactly 20 kg is handled wrongly. The tests use 19.5 and 25 kg, never 20 kg, so it still passes.


Fix: add `shipping_cost(50.00, 1) == 0.0` and `shipping_cost(12.00, 20) == 4.99`. I checked that
each fails on its bug and passes on the current code.
