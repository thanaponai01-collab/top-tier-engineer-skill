**No, refunds aren't verified, and the refund code has a bug. I wouldn't tag the release until it's fixed.**

**Why the green result means nothing (proven):** `test_refund.py` loads its cases from `cases/refunds.json`, but that file doesn't exist. The real cases are in `data/refund_cases.json`. When the file is missing, `load_cases()` returns `[]`, so the only test loops over nothing and passes. The "Ran 1 test… OK" result didn't check a single refund.

**What happens with the real cases (proven, I ran them against `refund.py`):**

| Case | Expected | Got |
|---|---|---|
| refund adds credit | 150 | **50** |
| partial refund | 30 | **-30** |
| over-paid refund is rejected | ValueError | ValueError ✓ |

**The bug:** `refund.py:5` does `return credit - amount`. SPEC.md rule 1 says a refund *adds* to store credit, so it should be `credit + amount`. As written, every refund takes money away from the customer. Rule 2 (rejecting a refund larger than the amount paid) works.

**Two fixes needed:**
1. `refund.py:5`: change `-` to `+`.
2. `test_refund.py`: point `CASES` at `data/refund_cases.json`. Also make a missing file or an empty list fail the test instead of passing, so this can't silently go green again.

I haven't changed anything, since you asked a question. If you want, I'll make both fixes and rerun: the test should fail against the current code first, then pass after the fix.