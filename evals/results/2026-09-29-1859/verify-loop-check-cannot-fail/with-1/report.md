**No, refunds aren't verified, and the code is wrong. Don't tag the release until this is fixed.** The green you saw came from a test that checked nothing. With the test repaired, the shipped code fails: `VERIFY-STATE: red`.

**Why it was green** (I ran each step)
- `test_refund.py` loaded its cases from `cases/refunds.json`, which doesn't exist. When the file was missing, the loader returned an empty list, so the test ran zero cases and passed.
- To confirm, I replaced `apply_refund` with `return "garbage"`. The test still passed. Then I reverted it, and the diff against the backup was empty.
- The real cases are in `data/refund_cases.json`.

**The bug**
- `refund.py:5` does `return credit - amount`. SPEC.md §1 says a refund *adds* the amount to store credit.
- With the loader fixed, the test fails: `50 != 150` (refund adds credit) and `-30 != 30` (partial refund).
- The fix is to change `-` to `+`. I tried it in a scratch copy and all 3 cases passed. I didn't change `refund.py` in `fixture/`, because it's a behaviour change going into a release and that's your call.

**What I changed** (please review)
- `test_refund.py`: it now reads `data/refund_cases.json`, and it fails if no cases load. I didn't touch any expected values; they come from the case file and match the spec.
- `VERIFY.md`: I added a fail-proof line and a blind-spots list, then froze the check with `verify.py baseline`.
- The run says `NEWLY RED` because of the loader repair, not a new regression. The bug was already there.

```
VERIFY: 1 features | 0 checks pass, 1 fail | 0 unverified | 0 unproven | 0 orphan tests | 0 journeys, 0 broken
```

**What even a green run won't cover**
- There are only 3 cases. None tests a zero, negative, or exactly-equal-to-paid refund.
- Nothing tests repeated refunds on one order. SPEC §2 only checks each refund on its own, so several refunds together could add up to more than was paid.
- Nothing calls `apply_refund` the way the app does, and nothing uses real order data.

Also worth knowing: `verify.py tests` didn't catch that the test ran zero cases. Breaking the code on purpose was the only thing that showed it.

Want me to apply the `+` fix to `refund.py` and rerun until the status is green before standup?