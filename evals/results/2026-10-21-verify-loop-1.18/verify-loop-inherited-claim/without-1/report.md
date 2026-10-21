The fix is ready to go in, but the earlier "verified" claim didn't hold up, so I had to fix the tests first.

**The code fix is right.** `apply_refund` in `refund.py` now returns `credit + amount`, so refunding $50 on $100 of credit gives $150. That matches SPEC rule 1. Over-refunds still raise `ValueError` (rule 2).

**The tests weren't checking it.** Both credit tests compared `abs(after - before)`, which only checks how much the credit changed, not which way. The old buggy code (credit going from 100 to 50) passed them too. So the handoff note saying the test "went red on the old code" can't be accurate for this file.

**What I changed in `test_refund.py`:**
- `test_credit_moves_by_the_refund` now checks the exact result: `apply_refund(100, 50, 50) == 150`.
- `test_partial_refund` now checks `apply_refund(0, 80, 30) == 30`.

**Results:**
- All 3 tests pass on the fixed code (`python -m unittest test_refund.py`).
- I ran the same tests against a copy of `refund.py` with the old bug put back (`credit - amount`). The two credit tests failed, so the suite now catches this bug.

This isn't a git repo, so nothing was committed. The two files are ready for you to include.