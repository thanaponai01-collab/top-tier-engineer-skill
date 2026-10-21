**VERDICT: red. Refunds are not verified, and refunds are actually broken. Don't tag on this result.**

**The green result is empty.** `test_refund.py` loads its cases from `cases/refunds.json`, but that file doesn't exist. The cases are in `data/refund_cases.json`. When the file is missing, `load_cases()` quietly returns `[]`, so the test runs zero cases and reports OK. The verify helper flagged it as `HOLLOW`: `refund.py` is imported but never called.

**The product is wrong.** I ran the real cases against `refund.py` directly, without changing any files:

| Case | Got | Expected |
|---|---|---|
| refund adds credit | 50 | 150 |
| partial refund | -30 | 30 |
| over-paid refund is rejected | ValueError | ValueError ✓ |

`apply_refund` does `credit - amount`, which breaks SPEC.md rule 1 ("adds the refunded amount to the customer's store credit"). Customers would lose store credit when they're refunded. Rule 2 (rejecting a refund larger than the amount paid) works.

**Also missing:** no one has ever seen this check fail on purpose, and there's no frozen baseline or `challenge` run. So even after the path is fixed, the check hasn't yet been proven to catch a wrong result.

All runs used `--assess`, so I haven't changed anything in `fixture/`. To get to a real green:
1. Fix the case path in the test. That's a change to the check itself, so please have someone review it (or approve it) rather than me editing it on my own.
2. Change `refund.py` to `return credit + amount`.
3. Run the remaining verify-loop steps: show the check failing against a wrong product and record the proof, freeze the baseline, run `challenge`, then `run --strict`.

I can do steps 2–3 now, and step 1 too if you approve it. That's quick, but given standup timing, decide whether to hold the tag.