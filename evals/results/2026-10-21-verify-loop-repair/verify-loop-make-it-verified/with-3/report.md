Refunds are now verified (`VERDICT: green`), but only after I changed both the test and the product code. Please look over those changes before you tag the release.

**Before my changes, the refund test passed without checking anything.** It loaded its cases from `cases/refunds.json`, which doesn't exist; the data is in `data/refund_cases.json`. When the file was missing it quietly ran zero cases, so the green result said nothing about refunds.

**Once the test actually ran, it found a real bug.** `apply_refund` subtracted the refund from store credit (`credit - amount`). SPEC.md rule 1 says a refund adds to it. A $30 refund on $0 credit gave -30 instead of 30.

**What I changed in `fixture/`:**
- **`test_refund.py`:** points at `data/refund_cases.json`, and now fails if the file is missing or empty instead of silently passing.
- **`refund.py`:** `credit - amount` → `credit + amount`. I froze the test before making this fix, so the fix couldn't be made to pass by adjusting the test.
- **`VERIFY.md`:** added which product file the test covers, where the expected results come from (SPEC.md and the cases file), the failure message to watch for, and how the test was proved able to fail.

**Evidence that the test can catch a broken refund:**
- Putting the subtraction bug back makes the test fail on "refund adds credit" and "partial refund"; restoring the fix makes it pass.
- Automated mutation testing changed `refund.py` in 3 different ways, and the test caught all 3.
- The final strict run and status check both report green, and the written summary passed the helper's answer check.

**Limits:**
- I froze the test and then judged the result myself; no independent reviewer was involved.
- Green covers only what SPEC.md and the three test cases describe.
- `fixture/` isn't a git repository, so nothing was committed.