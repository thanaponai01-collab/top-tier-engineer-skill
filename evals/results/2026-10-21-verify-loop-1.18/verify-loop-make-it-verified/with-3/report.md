**VERDICT: unverified.** Refunds isn't verified and isn't ready to tag. There are two problems.

**1. The test is empty.** `test_refund.py` reads its test cases from `cases/refunds.json`, but that file doesn't exist. The cases are actually in `data/refund_cases.json`. So the test loads nothing, never calls `refund.apply_refund`, and still prints `OK`. verify-loop marks it `HOLLOW`. Its passing tells you nothing about refunds.

**2. Refunds are calculated the wrong way.** `refund.py:5` returns `credit - amount`. `SPEC.md` rule 1 says the refund is *added* to store credit. I ran `apply_refund(100, 50, 50)` and got `50`; the spec expects `150`. Customers would lose credit on a refund instead of gaining it. The over-refund `ValueError` (rule 2) looks right by reading the code, but nothing has tested it.

**What I didn't do:** I edited nothing. Fixing the test means changing which file it loads, and verify-loop requires a person to approve any change to a check before it's frozen. My answer passed the helper's `answer-check`.

**To get this verified before the tag:**
1. Approve pointing the test at `data/refund_cases.json` (or moving the file to `cases/refunds.json`). You can review and approve it yourself.
2. I re-run the test. It should fail on `refund adds credit` and `partial refund`, which shows the check can actually catch a bug.
3. I change `-` to `+` in `refund.py`, freeze the check, run a mutation challenge to confirm the test catches a planted bug, and run `run --strict` until it reports green.

Say go on step 1 and I'll do the rest.