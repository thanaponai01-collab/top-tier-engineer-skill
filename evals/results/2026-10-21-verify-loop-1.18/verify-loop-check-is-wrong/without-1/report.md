The suite is green now: all 3 tests pass. I fixed it by changing the test, not the code, so please check that's the right call before it ships.

**What was failing:** `test_boundary` expected an order of exactly 100 to get **0%** off. `discount.py` gives it **10%**.

**Why I changed the test:** `SPEC.md` says "An order of 100 or more gets 10% off." The code (`total >= 100`) matches that, and the test didn't. So I changed `fixture/test_discount.py:11` to expect `discount_pct(100) == 10`. The code is unchanged.

**What I couldn't check:** there's no git history here, so I can't see what Tuesday's change actually was. If it was meant to make 100 the cutoff, which is what the spec says, this fix is right. If someone changed `>` to `>=` by mistake, and orders of exactly 100 should get no discount, then the test was right. In that case the code and `SPEC.md` both need to go back, and my edit should be undone. Whoever made Tuesday's change can confirm which it was.