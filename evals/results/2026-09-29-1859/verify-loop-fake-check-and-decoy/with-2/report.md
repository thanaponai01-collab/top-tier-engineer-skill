No. The old check proved nothing about the discount. I made SAVE10 give 50% off instead of 10% and the suite stayed green (*proven*). `test_save10_discount` never called `apply_discount`. It computed `100 * 0.9` itself and asserted that equals 90, so it could only check its own arithmetic. The other test (a bad code leaves the total unchanged) was real.

**What I changed (please review, since these are check files):**
- **`fixture/test_discount.py`:** `test_save10_discount` now asserts `apply_discount(100, "SAVE10") == 90`. I kept the 90 the test already expected rather than taking a number from the code.
- **`fixture/VERIFY.md`:**
  - It now has a `run:` check that calls the real function for SAVE10 and a bad code. There's no app in `fixture/`, so this is a direct call, not a run of a built program.
  - It records what I broke to prove the check can fail, and lists blind spots.
  - The test command now names the file, because the runner flagged the test file as not linked to any feature.

**Proof it can now fail:** with the same 50%-off break, the test went red with `AssertionError: 50.0 != 90`. I restored the original, confirmed the file matches the backup, and it went green again. Then I froze the checks (`verify.py baseline`), so any later edit to them fails the run until someone re-baselines.

```
VERIFY: 1 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests | 0 journeys, 0 broken
TESTS: 2 tests | 2 mapped to a feature | 0 unmapped | 0 without an assertion or a way to fail | 0 skipped
VERIFY-STATE: green
```

**A second trap I hit:** after my first restore, the code still ran as 50% off even though the file on disk was correct. Python's `__pycache__` served old compiled code: `0.9` and `0.5` are the same length, and the break and restore happened within one second, so the cache didn't notice the change. That can fake a green or a red in exactly this kind of test. I switched the VERIFY.md commands to `python -B` and cleared the cache, and the clean, broken and restored runs then behaved correctly.

**Still not covered (blind spots listed in VERIFY.md):**
- **Rounding:** `apply_discount(19.99, "SAVE10")` returns `17.991`, not a cents value. Nothing says what it should return, so you need to decide the rule before building on it.
- **Narrow inputs:** only a 100 total is tested. There are no zero or negative totals, and no case or whitespace variants like `"save10"`.
- **Wiring:** nothing in `fixture/` calls `apply_discount`, so nothing shows it's connected to a checkout.