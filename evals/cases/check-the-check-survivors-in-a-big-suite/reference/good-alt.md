Two things would get through.

split_payment: none of the tests has a remainder. I changed `base + 1` to `base + 2` and the suite
stayed green; with that, 1000 split three ways gives parts that add to 1002. Test an uneven split.

Volume discount: exactly 20 seats is never priced. I moved the tier to (21, 10) in VOLUME_TIERS and
nothing failed. 20 seats should get 10% off.

Everything else I mutated was caught.
