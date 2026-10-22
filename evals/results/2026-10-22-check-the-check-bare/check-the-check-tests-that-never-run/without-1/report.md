No. The claim is false, and the headline feature itself is broken.

**1. The gold-points tests never run.** I ran the suite and it reports `Ran 2 tests ... OK`. Those two are the redeem tests. The three tests in `PointsEarnedTest` (including `test_gold_earns_double`) are never collected. The class inherits only from `PointsFixtures`, and `PointsFixtures` in `points_fixtures.py` is a plain class, not a `unittest.TestCase`, so unittest doesn't see them. CI is green because it isn't testing gold points at all.

**2. Gold members don't earn double points.** `points.py:4` doubles points for the wrong tier:
```python
return base * 2 if tier == "silver" else base
```
I checked it directly: `points_for(42.99, 'gold')` returns **42**, not 84. `'silver'`, which isn't in the spec, returns 84. If the tests did run, `test_gold_earns_double` would fail.

**Where each release note stands:**
- "Gold members now earn double loyalty points. Covered by test_points.py": **false.** The code is wrong and its tests don't run.
- "Redeeming more points than you have is now rejected": **true.** `test_overdraw_is_rejected` runs and passes, and the code matches SPEC.md item 3.

**What would make it signable:**
1. Change `"silver"` to `"gold"` in `points.py:4`.
2. Have `PointsFixtures` inherit from `unittest.TestCase`, or declare `class PointsEarnedTest(PointsFixtures, unittest.TestCase)`.
3. Re-run and confirm the output says `Ran 5 tests`, not 2. That count is the quickest way to check CI is actually running the earning tests.

I haven't changed any files. I can make those two fixes if you want, though it's probably also worth finding out where "silver" came from before shipping.