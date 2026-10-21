**VERDICT: unverified.** Refunds aren't verified, and the refund code is wrong. Hold the tag.

**The green is hollow.** `test_refund.py` loads its cases from `cases/refunds.json`, but that file doesn't exist; the cases are in `data/refund_cases.json`. When the file is missing, `load_cases()` returns `[]`, so the test runs zero cases and reports `OK` without ever calling `apply_refund`. The verify-loop helper flags this as `HOLLOW`, and the check has never been seen to fail.

**The code is wrong.** `refund.py` does `return credit - amount`, but `SPEC.md` rule 1 says a refund *adds* to store credit. Calling it directly:
- `apply_refund(100, 50, 50)` returns `50`; the spec expects `150`
- `apply_refund(0, 80, 30)` returns `-30`; the spec expects `30`

The over-refund `ValueError` (rule 2) looks right when read, but no check actually runs it.

I didn't change anything. Fixing the test's path is an edit to the check itself, so I'm leaving that for you to decide on. The fix I'd suggest:
1. Point `CASES` at `data/refund_cases.json`. Also make a missing file fail the test instead of returning `[]`, so this can't pass with zero cases again.
2. Re-run the test. It should fail on the two credit cases, which confirms the check can catch a wrong result.
3. Change `refund.py` to `credit + amount` and re-run until it passes.
4. Then do the rest of the proof: record the failure in `VERIFY.md` (with a `fail-signal:`), freeze the check with `baseline`, run `challenge`, then `run --strict`.

Want me to go ahead once you've approved the test change?