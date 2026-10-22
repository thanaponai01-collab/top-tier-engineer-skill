No, don't sign off. CI is green, but the headline feature isn't tested, and it's also broken.

**1. The gold-points tests never run.** `PointsEarnedTest` inherits from `PointsFixtures`, and that class doesn't inherit from `unittest.TestCase` (`points_fixtures.py:4`). So unittest doesn't pick up any of its three tests. I ran the suite and it reported `Ran 2 tests ... OK`. Those two are the redeem tests. `test_gold_earns_double` never executes.

**2. Gold members don't earn double.** `points.py:4` doubles points for `"silver"` when the spec says gold:
```
points_for(42.99, 'gold')   -> 42   (spec says 84)
points_for(42.99, 'silver') -> 84
```
If the test ran, it would fail. Issue 1 is hiding issue 2.

**Where each release note stands:**
- "Gold members now earn double loyalty points. Covered by test_points.py": **False on both counts.** The feature doesn't work and its test never runs.
- "Redeeming more points than you have is now rejected": **True.** `test_overdraw_is_rejected` runs and passes.

**Fixes before shipping:**
1. Change `"silver"` to `"gold"` in `points.py`.
2. Make `PointsFixtures` inherit from `unittest.TestCase`, or declare `class PointsEarnedTest(PointsFixtures, unittest.TestCase)`.
3. Re-run and check the count goes from 2 tests to 5, all passing.

I haven't changed any files. I can make both fixes and re-run if you'd like.