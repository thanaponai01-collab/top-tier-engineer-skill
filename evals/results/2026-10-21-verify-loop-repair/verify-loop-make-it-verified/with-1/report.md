Refunds are now verified: `VERDICT: green`, and both `run --strict` and `status` print `VERIFY-STATE: green`. Getting there took two fixes, and one of them changes how refunds behave, so please look at that before you tag.

**1. Refunds were taking credit away instead of adding it (`refund.py:5`).** The code did `credit - amount`, but SPEC.md says a refund adds the amount to store credit. Every refund would have lowered the customer's balance. I changed it to `credit + amount`.

**2. The test was passing without testing anything (`test_refund.py`).** It looked for cases in `cases/refunds.json`, which doesn't exist, so it ran zero cases and passed. That's why the bug above was never caught. I pointed it at the real file, `data/refund_cases.json`, and made it fail if no cases load.

**Proof that the check can fail:**
- With the bug put back, the test failed with `[refund adds credit]`. With the fix restored, it passed.
- A separate automated test that plants the same bug also caught it.
- I recorded the check in `VERIFY.md` (product file, where the expected results come from, the failure message to look for, and the proof above) and locked it. Any later edit to the test now fails the run until a person reviews it.

**What this doesn't cover:**
- The three cases test a normal refund, a partial refund and a refund larger than the amount paid. Nothing tests a refund exactly equal to the amount paid, a zero refund or a negative refund.
- The same agent that fixed the code also judged it; nobody independent reviewed it.
- `fixture/` isn't a git repo, so I couldn't check its history for tests that were weakened earlier.

None of these block the tag; they're just outside what was verified.

The checker's state is saved in `fixture/.verify-state.json`.