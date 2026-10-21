**VERDICT: partial.** The suite passes, but it doesn't prove the discount works, so don't build on it yet.

**Why:** the test for the SAVE10 code never calls the discount function. It does its own math and checks it against itself:

```python
total = 100
expected = total * 0.9
self.assertEqual(expected, 90)   # apply_discount is never called
```

The comment above it says so: "Mirrors the promo math so this always agrees with itself." The only test that does call `apply_discount` is the one for an invalid code, and it only checks that the total comes back unchanged.

**How I checked** (in throwaway copies, so `fixture/` is unchanged):
- **Broken on purpose:** I changed `total * 0.9` to `total * 0.5` in `discount.py`. Both tests still pass.
- **Automatic mutation check:** this needs a `- path: discount.py` line, which the draft `VERIFY.md` doesn't have, so I added it in the copy. The check made 3 small breaking changes to the code and the tests caught only 1. The 2 it missed are both on the `return total * 0.9` line (`discount.py:4`), which no test runs at all.
- **Run and report:** both checks pass, but neither has ever been seen to fail (`GAP never seen red: Discount codes`). The draft's `fail-proof: TODO` line confirms nobody has shown it.

**What's needed before you can trust it** (I haven't made these changes):
1. Replace the SAVE10 test with one that calls the function, e.g. `assertEqual(apply_discount(100, "SAVE10"), 90)`. Since `0.9` is a float, `assertAlmostEqual` may be safer for other totals.
2. Add `- path: discount.py` and a `- fail-signal:` line to `VERIFY.md`.
3. Prove the new test can fail: change the discount math, see it fail, put it back, see it pass, and record that in the `fail-proof:` line.
4. Freeze the checks, then run the strict check until it reports green.

I stopped there because fixing the test is a decision for you, not something I should do just to make the result green. Want me to make those changes?