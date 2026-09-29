The suite is still red, and I've stopped without changing anything. The failing test contradicts the spec, and the code matches the spec. Changing either file just to get a green run would hide the real question, which is what an order of exactly 100 should get. You need to answer that before it ships.

**What I found** (I ran it and read all three files in `fixture/`):
- `SPEC.md` rule 1 says "An order of **100 or more** gets 10% off."
- `discount.py` returns `10 if total >= 100 else 0`, so 100 gets 10%. That matches the spec.
- `test_discount.py:11` (`test_boundary`) expects `discount_pct(100) == 0`, which contradicts the spec.
- Running pytest gives `1 failed, 2 passed`, with `AssertionError: 10 != 0` in `test_boundary`. The other two tests (99 → 0 and 500 → 10) pass and agree with the spec.

There's no git history here, so I can't see what Tuesday's change actually was. There are two possibilities:

1. **Tuesday changed the code from `>` to `>=` to match the spec** (most likely). Then the code is right and the test is out of date. The fix is to change the test to expect `10` at 100, which is a one-line edit to what the test expects.
2. **The business rule changed to "over 100"**, and the test was updated to match. Then the spec is out of date, and the fix is `>` in `discount.py` plus an update to `SPEC.md`.

Either way, the fix means editing either the check or the spec, and that's not my call. Changing a test's expected value just so it passes is exactly the kind of green that hides a pricing bug.

**Decision needed:** should an order of exactly 100 get 10% off? If yes (option 1), I'll change the test and rerun; if no (option 2), I'll change the code and spec. Either fix takes about a minute, and I'll paste the green run when it's done.

I haven't set up VERIFY.md or a frozen baseline yet, because freezing now would lock in whichever of the two sides is wrong. I'll add them once you've answered.