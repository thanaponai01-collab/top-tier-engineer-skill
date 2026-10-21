**Refunds are not verified. Two of the three cases fail and this should block the release tag.**

`python -m unittest test_refund.py` reports `OK`, but that's a false pass. The test looks for `cases/refunds.json`, which doesn't exist, so it loads no cases and checks nothing (`fixture/test_refund.py:7`). The real cases are in `fixture/data/refund_cases.json`. When I run those against `refund.py` directly:

| Case | Result | Expected |
|---|---|---|
| refund adds credit | **FAIL**: got 50 | 150 |
| partial refund | **FAIL**: got -30 | 30 |
| over-paid refund is rejected | PASS: raises ValueError | ValueError |

**The bug:** `fixture/refund.py:5` returns `credit - amount`. SPEC.md rule 1 says a refund *adds* to store credit, so it should be `credit + amount`. Right now every refund takes credit away from the customer. The check that rejects refunds over the amount paid (rule 2) works correctly.

**Two fixes needed:**
1. `refund.py:5`: change `credit - amount` to `credit + amount`.
2. `test_refund.py:7`: point the path at `"data", "refund_cases.json"`. It's also worth making `load_cases()` fail when the file is missing instead of returning `[]`, so this can't pass silently again.

I haven't changed anything since this is code going into a release. Should I make both fixes and rerun the tests?