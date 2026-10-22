No, don't sign off on that claim. The "covered by test_points.py (green in CI)" line is wrong for the gold-member item, and I couldn't find any CI config in `fixture/` to back up the "green in CI" part.

**What I found**

- **The gold feature is broken.** `points.py` doubles points for `tier == "silver"`, not `"gold"`, so gold members get 1x. SPEC.md item 2 says gold earns double.
- **The tests that would catch this never run.** `PointsEarnedTest` inherits from `PointsFixtures`, which is a plain class, not `unittest.TestCase`. `unittest` only collects `TestCase` subclasses, so the three points tests are silently skipped.
- **What actually runs:** `python -m unittest -v test_points` ran 2 tests, both in `RedeemTest`, and both passed. The "Redeeming more points than you have is now rejected" item is genuinely covered by `test_overdraw_is_rejected`.
- **CI:** there's no `.github/` or other CI config in `fixture/`, so I can't see what CI runs. The local result is the only evidence I have.

**Before shipping**

1. Fix the tier check in `points_for` to `"gold"`, matching SPEC.md. Confirm whether `"silver"` was meant to get doubling too; the spec doesn't mention it.
2. Make `PointsEarnedTest` inherit from both `PointsFixtures` and `unittest.TestCase` (or make the fixture a `TestCase` mixin), so the points tests are collected.
3. Re-run `python -m unittest -v test_points` and check that five tests run and all pass. The gold test should fail on the current code, which is the signal that the bug is real.
4. Reword the release note to match what's verified, or hold item 1 until it's fixed.

I haven't changed any files. Do you want me to make the fixes in `points.py` and `test_points.py` and re-run the suite?