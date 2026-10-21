**No, refunds aren't verified.** The green VERIFY.md result is a false pass, and the refund code has a real bug.

**1. The test runs zero cases.** `test_refund.py` reads `cases/refunds.json`. If that file doesn't exist, `load_cases()` returns `[]` instead of failing. The real data is at `data/refund_cases.json`, so the path is wrong, the loop never runs, and the test reports `OK` without checking anything.

**2. Refunds subtract credit instead of adding it.** I ran `fixture/refund.py:5` (`return credit - amount`) against the actual case file:

| Case | Got | Expected |
|---|---|---|
| refund adds credit | 50 | 150 |
| partial refund | **-30** | 30 |
| over-paid refund is rejected | ValueError | ValueError ✓ |

This breaks rule 1 of SPEC.md ("adds the refunded amount to the customer's store credit"). Every refund would take credit away from the customer, and it can push their balance negative. Only the rejection rule (rule 2) works.

**What to fix before tagging:**
- `refund.py:5`: change it to `return credit + amount`.
- `test_refund.py`: point `CASES` at `data/refund_cases.json`, and make a missing file fail the test instead of returning `[]`. Also add a check that at least one case was loaded, so this can't silently pass again.

I haven't changed anything. I'd hold the tag until both fixes are in and the test fails before the code fix and passes after it. I can make the changes now if you want.