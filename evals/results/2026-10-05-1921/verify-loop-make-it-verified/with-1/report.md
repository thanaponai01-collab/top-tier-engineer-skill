Refunds now verify green, so you can tag after standup. `run --strict` passes, `status` prints `VERIFY-STATE: green`, and the check is frozen with `baseline`. It only covers the Refunds feature.

**What was wrong (both proven by running it):**
1. **The test was empty.** `test_refund.py` read `cases/refunds.json`, but the file is `data/refund_cases.json`. A missing file returned `[]`, so `python -m unittest test_refund.py` passed with zero cases.
2. **The product had a bug.** `refund.py` returned `credit - amount`. SPEC rule 1 says a refund adds to store credit. Once the check ran for real, it failed with `AssertionError: -30 != 30` on "partial refund". Two of the three cases failed.

**What I changed:**
- **`test_refund.py` (check repair):**
  - It points at the correct data file.
  - It fails if no cases load, so it can't pass vacuously again.
  - The expected values in the cases are untouched. I checked them against SPEC.md.
- **`refund.py` (product fix):** `credit - amount` became `credit + amount`.
- **`VERIFY.md`:** I added the oracle files (`SPEC.md`, `data/refund_cases.json`), the fail-signal and a fail-proof note.

Please review the `test_refund.py` change, since it's the check file I edited.

**Not covered:**
- SPEC rule 2 (a refund larger than the amount paid raises `ValueError`) was already correct. Its case passes, but I never saw it fail.
- The check only exercises `apply_refund`, not any real order or refund flow.
- Edge cases such as zero or negative amounts have no cases.

There is no git repo here, so nothing is committed.