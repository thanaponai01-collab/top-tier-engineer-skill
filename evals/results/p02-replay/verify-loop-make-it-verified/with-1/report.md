Refunds are **not verified**, and the release shouldn't be tagged on them yet. The test is green, but it was checking nothing, and refunds are broken.

`VERIFY: 1 features | 0 checks pass, 1 fail | 1 unproven` → `VERIFY-STATE: red`

**What I found**

1. **The test ran zero cases.** `test_refund.py` loaded `cases/refunds.json`, which doesn't exist, and quietly returned an empty list. The real cases are in `data/refund_cases.json`. I fixed the path and added a check that fails if no cases load. I didn't change any expected values; those come from `SPEC.md` and the data file.
2. **Refunds take money away from the customer.** With the test actually running, it fails. `fixture/refund.py:5` returns `credit - amount`, but SPEC rule 1 says a refund *adds* to store credit:
   - "refund adds credit": got 50, expected 150
   - "partial refund": got -30, expected 30
   - The over-refund rejection (rule 2) works.

**What I changed:** only the test (`test_refund.py`) and `VERIFY.md`. I added the expected-results files, the text a real failure prints, a note recording the failure above, and the blind spots. I haven't frozen the checks yet (that step is called `baseline`), so it's still open for your review.

**What I didn't do:** I didn't change `refund.py`. You asked me to verify, not to change product code, and this is a money bug, so I'm leaving that call to you. The fix is one character (`credit - amount` → `credit + amount`). Say go and I'll make it, freeze the checks, and run the strict check until the status reads green.

**Not covered even once it's green:**
- It's unit-level only. Nothing in `fixture/` calls `apply_refund`, so there's no full refund flow to test.
- There are no cases for zero or negative amounts, or for a refund equal to the amount paid. The spec doesn't say what should happen there.