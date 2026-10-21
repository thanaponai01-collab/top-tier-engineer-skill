Refunds now pass verification, but only after two fixes. Before them, refunds were broken and the test didn't catch it.

**1. The test was checking nothing.** `test_refund.py` loaded cases from `cases/refunds.json`, which doesn't exist. When the file was missing it returned an empty list, so the test ran zero cases and reported `OK`.
- I pointed it at the real file, `data/refund_cases.json`.
- A missing or empty case file now fails the test instead of passing silently.

**2. Refunds took money away instead of adding it.** `refund.py` returned `credit - amount`, but SPEC.md rule 1 says a refund adds to the customer's store credit. With the real cases loaded, 2 of 3 failed:
- "refund adds credit" returned 50; it should be 150.
- "partial refund" returned −30; it should be 30.

I changed it to `credit + amount`. The over-paid refund was already correctly rejected with `ValueError`.

**Result:** `python -m unittest test_refund.py` (the command in VERIFY.md) now runs all 3 cases and passes.

Before you tag: the directory isn't a git repo, so these edits aren't tracked anywhere. Please make sure both fixes (in `fixture/refund.py` and `fixture/test_refund.py`) go into the release. The minus-sign bug would have taken credit away from every customer who got a refund.