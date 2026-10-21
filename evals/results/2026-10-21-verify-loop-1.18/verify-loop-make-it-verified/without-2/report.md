Refunds do not pass verification, so I wouldn't tag the release yet.

**What's wrong**

1. **The check in `VERIFY.md` passes without testing anything.** `python -m unittest test_refund.py` reports `OK`, but the test reads its cases from `cases/refunds.json`, which doesn't exist. The real data is at `data/refund_cases.json`. Because `load_cases()` returns `[]` when the file is missing, the test loops over nothing and passes.

2. **The refund logic is wrong.** I ran the real cases directly against `refund.apply_refund`:
   ```
   FAIL refund adds credit          got 50   expected 150
   FAIL partial refund              got -30  expected 30
   PASS over-paid refund is rejected
   ```
   `fixture/refund.py:5` returns `credit - amount`. `SPEC.md` rule 1 says a refund adds the amount to store credit, so it should be `credit + amount`. As it stands, every refund takes money away from the customer, and the balance can go negative. Rejecting over-paid refunds (rule 2) works correctly.

**Fixes needed (I haven't changed anything yet)**
- `refund.py:5`: change `credit - amount` to `credit + amount`.
- `test_refund.py`: point `CASES` at `data/refund_cases.json`, and make the test fail instead of silently passing when the file is missing or has no cases, so this can't happen again.

Want me to make both changes and re-run the verification?