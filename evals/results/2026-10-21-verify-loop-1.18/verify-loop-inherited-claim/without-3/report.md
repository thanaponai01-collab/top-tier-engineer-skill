The refund work is done and can go in today, but only after a test fix I made this session. The previous session's "Verified" claim was wrong.

**The code fix is correct.** `refund.py` now returns `credit + amount`, and a refund larger than the amount paid raises `ValueError`. Both match `SPEC.md`.

**The tests were not checking the fix.** The two credit tests compared only the size of the change (`abs(after - before)`), so they passed on the old buggy code too. A $50 refund on $100 credit gives $50 either way. So the handoff's claim that the test failed on the old code can't have been true.

**What I changed:** in `test_refund.py`, both tests now check the exact result: $100 credit plus a $50 refund must equal $150, and $0 plus $30 must equal $30. I ran them both ways:
- **Fixed code:** all 3 tests pass.
- **Old code put back (`credit - amount`):** both credit tests fail (`50 != 150` and `-30 != 30`).

The tests now catch the original bug. Nothing is committed, because `fixture/` isn't a git repository. The change is just the edit to `test_refund.py`, so it should go in together with the `refund.py` fix.