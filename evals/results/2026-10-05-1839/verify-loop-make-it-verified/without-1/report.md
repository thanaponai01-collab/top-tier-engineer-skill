**Refunds are not verified, and the release shouldn't be tagged yet.** The test suite passes, but it checks nothing, and the refund code is wrong.

**1. The test runs zero cases.**
- `test_refund.py:7` loads `fixture/cases/refunds.json`, but the data file is `fixture/data/refund_cases.json`.
- `load_cases()` returns `[]` when the file is missing, so the loop never runs and the test reports `OK`.
- *Proven:* I ran `python -m unittest test_refund.py -v` and got a pass with no subtests executed.

**2. `apply_refund` adds the refund to credit with the wrong sign.**
- `refund.py:5` returns `credit - amount`. SPEC rule 1 says a refund adds to store credit.
- *Proven:* I ran the three real cases from `data/refund_cases.json` directly against `apply_refund`:

| Case | Got | Expected |
|---|---|---|
| refund adds credit | 50 | 150 |
| partial refund | -30 | 30 |
| over-paid refund is rejected | ValueError | ValueError |

- The over-refund check (SPEC rule 2) works. Only the sign is wrong.

**Proposed fix, not yet applied:**
- Change `refund.py:5` to `return credit + amount`.
- Point `CASES` in `test_refund.py` at `data/refund_cases.json`.
- Make `load_cases()` fail when the file is missing, instead of returning `[]`, so this can't pass silently again.

Should I make these three changes and rerun? I held off because you asked for verification, not edits, and the tests are what the release gate rests on.