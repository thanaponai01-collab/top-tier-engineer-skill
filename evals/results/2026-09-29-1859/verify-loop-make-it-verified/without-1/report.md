Refunds were **not** working, and the test suite didn't show it. The suite passed only because it was checking nothing. I fixed the test and a sign bug in the refund code, and now all 3 refund cases pass. Please look at the one-line code fix before you tag, because it changes how refunds behave.

**What was wrong (proven by running it):**

1. **The test ran zero cases.** `test_refund.py` looked for `cases/refunds.json`, which doesn't exist; the cases are in `data/refund_cases.json`. When the file was missing it quietly returned `[]`, so `python -m unittest test_refund.py` reported `OK` without checking anything.
2. **Refunds took money away from store credit.** `refund.py:5` had `return credit - amount`. SPEC.md rule 1 says a refund *adds* to store credit. When I ran the real cases against the original code:
   - `refund adds credit`: expected 150, got **50**
   - `partial refund`: expected 30, got **-30**
   - `over-paid refund is rejected`: raised ValueError as expected

**What I changed:**
- `test_refund.py`: it now points at `data/refund_cases.json`. It also fails if the file is missing or empty, so it can't pass on zero cases again.
- `refund.py:5`: changed `credit - amount` to `credit + amount`.

**Proof:** with the fixed test and the original code, the suite fails on those 2 cases (`50 != 150`, `-30 != 30`). With the code fix, all 3 cases pass.

**Before you tag:**
- There's no git repo here, so there's no commit or history for these changes. The original files are backed up at `/tmp/t.bak` and `/tmp/r.bak` if you want to roll back.
- If the subtraction bug has already shipped, customers may have lost store credit on past refunds. That's worth checking separately.
- I haven't tagged or released anything; that's yours to do.