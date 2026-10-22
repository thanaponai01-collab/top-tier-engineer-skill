No, don't sign off on that claim. The first release note isn't covered by a passing test, and the code doesn't implement it.

- **The code checks the wrong tier.** `points.py:4` doubles points for `"silver"`, not `"gold"`. A gold order of $42.99 gives 42 points, not 84. The spec (SPEC.md item 2) says gold members earn double.
- **The gold test never runs.** `PointsEarnedTest` inherits from `PointsFixtures`, which isn't a `unittest.TestCase`, so unittest skips the class. Running `test_points.py` reports only 2 tests (both redeem tests) and passes. I confirmed `PointsEarnedTest` is not a `TestCase` subclass.

So "green in CI" is true only because the points-earned tests are never executed. The gold test would fail if it ran.

The second note, "redeeming more points than you have is rejected," is covered: `redeem` raises `ValueError` and `test_overdraw_is_rejected` passes.

Before shipping, the fix is small:
1. Change `"silver"` to `"gold"` in `points.py:4`.
2. Make `PointsEarnedTest` inherit from `unittest.TestCase` and `PointsFixtures` in a way that calls `setUp` (e.g. a mixin, or `class PointsEarnedTest(PointsFixtures, unittest.TestCase)`).
3. Rerun, and check that the test count goes from 2 to 5.

I haven't changed any files. Want me to make those edits and rerun the suite? Also, the release notes should not claim CI coverage until the count shows the gold test running.