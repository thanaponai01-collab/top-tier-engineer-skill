**VERDICT: red.** Refunds are not verified, and they shouldn't be tagged as they are.

Two problems:

1. **The test checks nothing.** `test_refund.py` loads `cases/refunds.json`, but that file doesn't exist. The cases are actually in `data/refund_cases.json`. Because the file is missing, the test loads zero cases and passes without ever calling `apply_refund`. The verify-loop helper flagged this as `HOLLOW`.
2. **Refunds have a real bug.** I ran the actual cases against `refund.py`:
   - "refund adds credit" returned 50; expected 150
   - "partial refund" returned -30; expected 30
   - "over-paid refund is rejected" correctly raised `ValueError`

   `refund.py:5` returns `credit - amount`. The spec (`SPEC.md` item 1) says the refund should be added to store credit, so it should be `credit + amount`. As written, every refund takes money away from the customer's credit.

I haven't changed any code. Pointing the test at the right file means editing the check, and the skill's rules say a person has to approve that, so I need your decision. If you approve, I'll:
- point `CASES` at `data/refund_cases.json` (or move the data to where the test expects it),
- confirm the test then fails against the current code and record that as the fail-proof,
- change `refund.py` to `credit + amount`,
- freeze the check, run a mutation challenge and do a strict run to get it to green.

The helper's assess mode, which I used, didn't write any state into `fixture/`.