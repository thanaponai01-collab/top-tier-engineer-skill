**Refunds were broken, and the existing test couldn't catch it.** I fixed a one-character bug in `refund.py`, and refunds now pass verification: `VERIFY-STATE: green`. Please review that fix before you tag the release, because it changes how money is calculated.

**What was wrong (proven by running it):**
1. **The test checked nothing.** `test_refund.py` loaded its cases from `cases/refunds.json`, which doesn't exist, so it ran zero cases and passed anyway. The real cases are in `data/refund_cases.json`.
2. **Refunds took money away instead of adding it.** `refund.py` did `return credit - amount`, but SPEC item 1 says a refund adds to store credit. Once the test ran its cases, it failed on the current code: `50 != 150` and `-30 != 30`. Customers would have lost credit on every refund.

**What I changed:**
- `refund.py:5`: `credit - amount` → `credit + amount`. This is the code fix to review.
- `test_refund.py`: I only fixed the test's plumbing. It now reads the right cases file, and it fails if no cases load, so it can't pass silently again. The expected values are unchanged, and they match SPEC.md.
- `VERIFY.md`: I added a second check that calls the refund function directly and expects 10 + 5 = 15. It also records how the checks were shown to fail and the blind spots below.

**Result:** `VERIFY: 1 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests`. `verify.py tests` found 1 test, tied to Refunds, with no empty or skipped tests. I froze the checks before fixing the code, so later edits to them will be flagged.

**What this doesn't cover:**
- There is no test for a refund exactly equal to the amount paid, for zero or negative amounts, or for amounts with cents.
- `fixture/` contains only the calculation, with no code that calls it or saves the new credit. So this proves the calculation is right, not that refunds work end to end.
- `fixture/` isn't a git repository, so there's no diff to review. The changed lines are listed above.