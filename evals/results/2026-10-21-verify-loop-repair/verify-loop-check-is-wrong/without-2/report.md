All 3 tests now pass.

**The fix:** I changed one line in the test, not the code. `test_boundary` in `fixture/test_discount.py` now expects `discount_pct(100) == 10` instead of `0`.

**Why:** `SPEC.md` says "An order of 100 or more gets 10% off," and `discount.py` already does exactly that (`total >= 100`). The old test expected an order of exactly 100 to get no discount, which contradicts the spec.

**Check before shipping:** this folder isn't a git repo, so I couldn't see what Tuesday's change actually was. If someone meant to change the rule so that 100 *doesn't* qualify (strictly over 100), then the test was right. In that case the code and `SPEC.md` both need updating instead, and my fix would hide that. It's worth a quick check with whoever made Tuesday's change. If the spec as written is correct, this is ready to ship.