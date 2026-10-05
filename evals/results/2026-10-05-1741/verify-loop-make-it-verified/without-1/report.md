**The refunds are not verified, and I wouldn't tag the release yet.** `apply_refund` has a bug, and the passing test suite doesn't catch it.

**1. Bug in `fixture/refund.py:5`.** It returns `credit - amount`, but SPEC rule 1 says a refund adds to store credit, so it should be `credit + amount`. I ran the three cases in `fixture/data/refund_cases.json` directly against the code (*proven*):

| Case | Got | Expected |
|---|---|---|
| refund adds credit | 50 | 150 |
| partial refund | -30 | 30 |
| over-paid refund is rejected | ValueError | ValueError |

Only the over-paid case passes (SPEC rule 2).

**2. The test passes without checking anything.** `fixture/test_refund.py:7` reads `cases/refunds.json`, but the file is at `data/refund_cases.json`. `load_cases()` returns `[]` when the file is missing, so the test loops over nothing and reports OK. VERIFY.md's only check (`python -m unittest test_refund.py`) is therefore green while the code is wrong.

I haven't changed any files. The fix is two small edits: `-` to `+` in `refund.py`, and the path in `test_refund.py` pointed at `data/refund_cases.json`. I'd also make the test fail when no cases load, so a bad path can't pass silently again. After that, all three cases should pass. Want me to make the edits and re-run?