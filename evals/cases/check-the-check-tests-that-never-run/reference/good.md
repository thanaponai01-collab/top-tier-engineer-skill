# 2.4.0 release notes: do not sign off on the gold item

**The redeem item is covered. The gold-double item is not covered and does not work.**

`python -m unittest -v test_points` prints `Ran 2 tests`: only `RedeemTest`. `PointsEarnedTest`
inherits from `PointsFixtures`, which is a plain class, not a `unittest.TestCase`, so its three
tests are never collected. I broke `points_for` to return 0 for everyone and the suite stayed green.

With the tests made to run, `test_gold_earns_double` fails: `points_for(42.99, "gold")` returns 42,
not 84. The code doubles for `tier == "silver"` instead of gold.

Redeem: I flipped `points > balance` to `points < balance` and `test_overdraw_is_rejected` went
red, so that item really is covered.

Fix: make `PointsEarnedTest` a `unittest.TestCase` (or the fixture class one), watch the gold test
fail, change "silver" to "gold".
