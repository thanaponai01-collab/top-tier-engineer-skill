**Refunds isn't verified, and I wouldn't tag the release on it.** The test passes, but it never actually tests anything. There's also a real bug in the refund code.

**1. The check tests nothing.** `test_refund.py` reads its cases from `cases/refunds.json`, which doesn't exist. When the file is missing, `load_cases()` returns `[]`, so the test loops over zero cases and reports `OK`. The helper confirms this: `HOLLOW — every check passed without calling a function in refund.py`. The real cases are in `data/refund_cases.json`.

**2. The refund code has a bug.** `refund.py:5` does `return credit - amount`, but SPEC.md rule 1 says a refund *adds* to store credit. I ran the real cases from `data/refund_cases.json` against the code directly:

| case | got | expected |
|---|---|---|
| refund adds credit | 50 | 150 |
| partial refund | -30 | 30 |
| over-paid refund is rejected | ValueError | ValueError ✓ |

So the green test is hiding a sign error that takes customers' credit away instead of giving it.

**What I didn't change:** I left both files alone. The process doesn't let me edit a check I think is wrong; a person has to approve that first. Fixing the code before the check works would mean nothing can show the fix is right.

**What I need from you:** OK to change `CASES` in `test_refund.py` to point at `data/refund_cases.json`? Alternatively, the file could move to `cases/refunds.json`. A missing cases file should probably also fail the test rather than pass. Once you approve, I'll:
1. Run the fixed check and confirm it fails on the current code, which proves it can catch the bug.
2. Record that failure and freeze the check.
3. Change `credit - amount` to `credit + amount`.
4. Run the strict check through to `VERIFY-STATE: green`.

**VERDICT: unverified.** The only check is hollow, and the code fails two of its three cases.