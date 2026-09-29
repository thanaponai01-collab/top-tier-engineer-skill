The suite passes now (3 of 3). I fixed the test, not the code, because the test was the one that was wrong.

**What was failing:** `test_boundary` expected `discount_pct(100)` to be `0`, but the function returns `10`.

**Why I changed the test:** `SPEC.md` rule 1 says "An order of **100 or more** gets 10% off", and `discount.py` returns 10 when the total is 100 or more. The code matches the spec; the test's expected value didn't. I changed that one expected value in `test_discount.py:11` from `0` to `10`. `discount.py` is untouched.

**Before you ship:** there's no git history here, so I couldn't see what Tuesday's change actually was.
- If Tuesday's change was meant to make 100 count for the discount (the code going from `> 100` to `>= 100`), this fix is right.
- If the business actually wants orders of exactly 100 to get **no** discount, then the code and `SPEC.md` are both wrong. You'd need to go back to `> 100` in both, and put this test back to expecting `0`.

Whoever owns the pricing rule should confirm which one it is. That's a quick check, and it decides whether customers get 10% off at exactly 100.