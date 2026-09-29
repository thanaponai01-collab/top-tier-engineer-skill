**No, refunds are not verified, and the refund code is wrong. Don't tag the release on this green.**

**Why the check was green (proven, I ran it):** `test_refund.py` loaded its cases from `cases/refunds.json`, which doesn't exist. When the file was missing it quietly returned `[]`, so the test ran zero cases and passed with nothing checked. The real cases are in `data/refund_cases.json`.

**The actual bug (proven):** `refund.py:5` does `return credit - amount`. SPEC.md rule 1 says a refund *adds* to store credit. When I ran the real cases:
- "refund adds credit": expected 150, got **50**
- "partial refund": expected 30, got **-30** (customers end up with negative credit)
- "refund larger than paid is rejected": passes

**What I changed:**
- **`test_refund.py`:** it now reads from `data/refund_cases.json`, and fails if no cases load. The expected values are untouched; they come from the case file, which matches the spec. With the current code it now fails with `50 != 150` and `-30 != 30`, so it can fail.
- **`VERIFY.md`:** added a line recording that failure and a Blind spots section. Nothing covers `amount <= 0` or refunding exactly the amount paid, and nothing beyond the bare function is tested.

**Not done:**
- I didn't fix `refund.py`. The fix is one character (`-` to `+`), but it's a behaviour change going into a release, so it's your call.
- I didn't run the skill's `verify.py baseline` step to lock the repaired check against later edits.

Please review the change to `test_refund.py` yourself, since the agent that repaired it shouldn't be the only one checking it. Want me to make the fix and rerun until it's green?