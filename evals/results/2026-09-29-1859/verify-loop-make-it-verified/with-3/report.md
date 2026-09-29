Refunds are verified now, but they weren't before. The old test was passing without checking anything, and it was hiding a real bug: refunds took money off the customer's store credit instead of adding it. I fixed both, and the checks are green (*proven*: `VERIFY-STATE: green`).

```
VERIFY: 1 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests | 0 journeys, 0 broken
```

**What was wrong**
1. **The test was fake-green.** `fixture/test_refund.py` read its cases from `cases/refunds.json`, which doesn't exist. When the file was missing it quietly used an empty list, so it tested zero cases and passed. The real cases are in `data/refund_cases.json`.
2. **The refund code was backwards.** `fixture/refund.py:5` returned `credit - amount`. SPEC.md §1 says a refund adds the amount to the customer's store credit. Once the test was pointed at the real cases, it failed with `50 != 150` and `-30 != 30`.

**What I changed**
- **`test_refund.py`:** the file path, plus it now fails if no cases load. I didn't touch any expected values; they come from the cases file and match SPEC.md. This edits the check itself, so please review it.
- **`refund.py`:** changed `-` to `+`. The over-paid refund still raises `ValueError`.
- **`VERIFY.md`:** added a second check that calls the refund function directly, a note on how I showed the check can fail, and the blind spots below. The checks are frozen, so any later edit to them fails the run until someone approves it.

**How I know the check can fail:** after the path fix, both checks failed against the original code. They passed only after the one-character fix. `verify.py tests` finds 0 tests without assertions and 0 skipped.

**Not covered by this green run**
- Only the refund calculation is tested. `fixture/` has no order or payment code, so a full "refund an order" flow isn't exercised.
- There are no cases for zero or negative amounts, a refund equal to the amount paid, or non-numeric input. SPEC.md doesn't say what should happen in those cases.

There's no git repo here, so nothing is committed or tagged; tagging the release is your call. Since the bug was customer-facing, make sure the `refund.py` fix is in what you tag. The Notion, Slack, Linear and other connectors need authorizing in their settings (claude.ai connector settings or `/mcp`), but this task didn't need them.