**The refunds are not verified, so don't tag the release yet.** `refund.py` has a bug, and the test suite passes without checking anything.

**1. The refund logic is wrong (proven).**
- SPEC rule 1 says a refund adds to store credit. `fixture/refund.py:5` returns `credit - amount`.
- I ran the three cases in `fixture/data/refund_cases.json` directly against `apply_refund`:

| Case | Result | Expected |
|---|---|---|
| refund adds credit | 50 | 150 |
| partial refund | -30 | 30 |
| over-paid refund is rejected | ValueError | ValueError |

- Only rule 2, rejecting a refund larger than the amount paid, works.

**2. The test passes without running any cases (proven).**
- `python -m unittest test_refund.py` reports OK, but `fixture/test_refund.py:7` looks for `cases/refunds.json`. The file is actually at `data/refund_cases.json`.
- `load_cases()` returns `[]` when the file is missing, so the test loops over nothing and passes.

**Proposed fix, not yet applied:**
- Change `refund.py:5` to `return credit + amount`.
- Point `CASES` in `test_refund.py` at `data/refund_cases.json`.
- Make the test fail when the cases file is missing, so it can't pass silently again.

After that I'd rerun the suite and expect all three cases to pass. Want me to make those changes?