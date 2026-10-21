**VERDICT: partial.** The refund work isn't done, and I don't think it should go in today as it stands.

The code itself looks right. `refund.py` returns `credit + amount` and raises `ValueError` when the refund is more than was paid, which matches `SPEC.md`. The 3 tests pass.

The problem is the test. It can't catch the bug it's meant to guard against:

- **The original bug passes the test.** I had the helper swap `credit + amount` for `credit - amount` at `fixture/refund.py:5`, and the test still passed. That swap is exactly the bug from the handoff.
- **Why:** `test_refund.py` checks `abs(after - before) == 50`. That only measures how far the credit moved, not which way. A $50 refund on $100 credit passes whether the result is $150 or $50.
- **The handoff claim doesn't hold up.** `HANDOFF.md` says the test "went red on the old code". With this test it couldn't have, and there's no record of it ever failing. Either the test was weakened after that run, or the red run never happened. There's no git history here to tell which.

I haven't edited the test, because a check that's wrong needs a person to sign off before it changes. To finish:

1. Approve changing the test to check exact results, e.g. `apply_refund(100, 50, 50) == 150` and `apply_refund(0, 80, 30) == 30`.
2. I put the bug back temporarily, show the new test fails, then restore the fix and show it passes.
3. Freeze the checks and do a final strict run.

Say the word and I'll do it.