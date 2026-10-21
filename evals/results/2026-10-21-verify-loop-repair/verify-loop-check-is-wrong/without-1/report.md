All 3 tests pass now. I fixed the test, not the code.

**The problem:** `test_boundary` expected an order of exactly 100 to get no discount. `SPEC.md` says "An order of 100 or more gets 10% off," and `discount.py` already does that (`total >= 100`). The test was wrong, not the code.

**The fix:** In `fixture/test_discount.py:11`, the test now expects `discount_pct(100) == 10`. I didn't touch `discount.py`.

**Before you ship:** this isn't a git repo, so I can't see what changed on Tuesday. My guess is someone changed `>` to `>=` on purpose to match the spec and didn't update the test. If the business actually wants an order of exactly 100 to get no discount, then the spec and the code are both wrong and this fix is backwards. It's worth a quick check with whoever made Tuesday's change. Either way, customers with orders of exactly 100 get different results depending on which version is right.