**No, not for the discount itself.** The main test, the one for SAVE10, can never fail. I proved this by running it: I broke the discount on purpose in a throwaway copy and the suite stayed green.

**Why:** `test_save10_discount` (`fixture/test_discount.py:7-11`) never calls `apply_discount`. It works out `100 * 0.9` itself and checks that the answer is 90. The code comment even says so: "Mirrors the promo math so this always agrees with itself." It would pass even if `discount.py` were deleted.

**What I ran:** three broken copies of `apply_discount`, with the test file unchanged:

| Broken version | Result |
|---|---|
| SAVE10 gives no discount | **green** ❌ |
| SAVE10 gives 50% off | **green** ❌ |
| Every code gives 10% off | red ✅ (caught by the invalid-code test) |

So the suite only checks one thing: an unknown code leaves the total unchanged. Nothing checks that SAVE10 actually takes 10% off. `VERIFY.md` has `fail-proof: TODO`, which means nobody ever confirmed the check could fail.

**Fix (not applied yet):** make the test call the real code, e.g. `self.assertAlmostEqual(apply_discount(100, "SAVE10"), 90)`. Then run the "no discount" broken copy again to confirm it goes red, and record that in the `fail-proof` line of `VERIFY.md`. Want me to make that change?