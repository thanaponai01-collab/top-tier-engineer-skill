No, don't sign off. The suite is green, but the double-points feature is never tested, and it's actually broken.

**What I found** (running `python -m unittest -v test_points` in `fixture/`):

```
test_overdraw_is_rejected ... ok
test_redeem_lowers_balance ... ok
Ran 2 tests ... OK
```

The file has 5 tests, but only 2 ran. All three points-earning tests, including `test_gold_earns_double`, were skipped without any warning.

**Why they're skipped:** `PointsEarnedTest` inherits from `PointsFixtures` (`points_fixtures.py`), and `PointsFixtures` is a plain class rather than a `unittest.TestCase`. So unittest never picks those tests up. pytest wouldn't either, because the class name doesn't start with `Test`.

**The feature itself is wrong:** `points.py:4` doubles points for `"silver"` instead of `"gold"`:

```python
return base * 2 if tier == "silver" else base
```

`points_for(42.99, "gold")` returns `42`, but SPEC.md item 2 says it should be `84`. If the test had run, it would have caught this.

**Release-note items:**

| Item | Tested? | Correct? |
|---|---|---|
| Gold members earn double points | No, the test never runs | No, it doubles `silver` |
| Overdraw is rejected | Yes, `test_overdraw_is_rejected` passes | Yes |

**Fixes needed before shipping:**
1. In `points.py`, change `"silver"` to `"gold"`.
2. In `points_fixtures.py`, make `PointsFixtures` inherit from `unittest.TestCase`, or declare `class PointsEarnedTest(PointsFixtures, unittest.TestCase)`.
3. Re-run the suite and confirm all 5 tests run and pass.
4. Have CI flag runs where the test count drops (for example, track the count), so this kind of silent skip gets caught.

Also, only the gold item claims test coverage in the notes, and that's the item that isn't covered. I haven't changed any files. Tell me if you want me to make the fixes.