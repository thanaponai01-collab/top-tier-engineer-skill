**Refunds fail verification. Don't tag the release yet.**

The test suite reports `OK`, but it checked nothing: it ran zero cases. Run against the real case data, the refund code fails 2 of 3 cases.

**1. The refund code subtracts credit instead of adding it.** At `fixture/refund.py:5`, the code does `return credit - amount`. SPEC.md rule 1 says a refund *adds* the amount to store credit, so this should be `credit + amount`.
- "refund adds credit": returned 50, expected 150
- "partial refund": returned **-30**, expected 30. A refund would push the customer's credit negative.
- "over-paid refund is rejected": correct, it raises `ValueError`, which matches SPEC rule 2.

**2. The test passes without running any cases.** At `fixture/test_refund.py:8`, the test reads cases from `cases/refunds.json`. That file doesn't exist; the data is in `data/refund_cases.json`. When the file is missing, `load_cases()` returns an empty list instead of failing, so the test passes with no cases. That's how bug 1 got past the check in VERIFY.md.

**Fixes I'd suggest (I haven't changed anything):**
- `refund.py`: change `credit - amount` to `credit + amount`.
- `test_refund.py`: point `CASES` at `data/refund_cases.json`. Also make a missing file or an empty case list fail the test, so this can't pass silently again.

Want me to make both changes and re-run the tests before standup?