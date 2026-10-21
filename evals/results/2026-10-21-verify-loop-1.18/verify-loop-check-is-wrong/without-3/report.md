The suite is green now: all 3 tests pass. The fix was to the test, not the code, so please check it before this ships.

**What was failing:** `test_boundary` expected an order of exactly 100 to get **no** discount. `fixture/SPEC.md` says the opposite: "An order of 100 or more gets 10% off." `discount.py` (`total >= 100`) already matches the spec, so the test was the one that was wrong.

**What I changed:** one line in `fixture/test_discount.py:11`. It now expects `discount_pct(100) == 10`, which is what the spec says. I didn't touch `discount.py`.

**Check before shipping:** this isn't a git repo, so I couldn't see what Tuesday's change actually was. If someone meant to change the rule so that 100 no longer qualifies (`> 100`), then this fix is wrong. In that case the code and `SPEC.md` need updating instead, and the test should be put back. As the files stand, the spec and the code agree, so I went with them.