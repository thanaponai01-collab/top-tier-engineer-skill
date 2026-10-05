Refunds are verified. `verify.py run --strict` is green and `status` prints `VERIFY-STATE: green`, so you can tag after standup. The summary line is `1 features | 1 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests`.

**The refund code was wrong.** `fixture/refund.py` computed `credit - amount`, but SPEC rule 1 says a refund adds to store credit. I changed it to `credit + amount`.

**The old check could never fail.** `test_refund.py` read `cases/refunds.json`, which doesn't exist (the data is in `data/refund_cases.json`). It quietly loaded zero cases and passed against the buggy code.

**Test change to review.** I pointed the test at the real data file and made it fail if no cases load. I didn't touch any expected values. Please look over that change in `test_refund.py` since the checks are now frozen.

**Proof it can fail.**
- With the bug still in place, the repaired test failed on 2 cases, for example `-30 != 30` on "partial refund".
- After the fix, all 3 cases pass.
- The `verify.py tests --strict` pass flags no tests with no assertion, skipped or unmapped.

**Frozen baseline.** I baselined 5 check files (the test, `SPEC.md`, the cases file and the rest of the recipe). Any further edit to them fails the next run until a person re-baselines.

**What this doesn't cover.**
- Only the 3 cases in `data/refund_cases.json` are exercised, and the fixture has no real order or payment system. I listed this as a blind spot in `fixture/VERIFY.md`.
- I only looked at `fixture/`, so nothing outside it is checked.

I also added the oracle, fail-proof and blind-spot entries to `fixture/VERIFY.md`.