I changed `fixture/total.py` so `total` returns `base + fee` instead of `base - fee`. The existing test, `test_total_includes_fee`, now passes. It expects `total(10, 2)` to equal 12.

I read `pick-skill` and it didn't route to any skill. This was a one-line fix with a known cause, so I did it directly.