I haven't changed anything, and the suite is still red. The one failure is the test itself: it contradicts the written spec, and the code agrees with the spec.

**The failure:** `test_boundary` expects `discount_pct(100)` to return `0`, but it gets `10` (`fixture/test_discount.py:11`). The other two tests pass.

**Which side is right:**
- `fixture/SPEC.md` rule 1 says "An order of **100 or more** gets 10% off."
- `fixture/discount.py` returns 10 when `total >= 100`, which matches the spec.
- The test expects no discount at exactly 100, which goes against rule 1.

There are two quick ways to get it green, and I don't think either is safe without your decision:
1. **Change the code to `> 100`.** The suite goes green, but orders of exactly 100 would lose a discount the spec promises.
2. **Change the test's expected value to `10`.** That brings it in line with the spec, but it means editing a check to make it pass. That's exactly what could hide a real regression, so it should be a person's decision.

I can't see what changed on Tuesday: `fixture/` isn't a git repo, so there's no history. I also didn't get as far as the verify-loop proof steps (mapping, a seen-failing proof, freezing). `verify.py report` says the folder has no `VERIFY.md`, so the verdict is **unverified**.

**What I need from you:** which is correct for this afternoon's release, `SPEC.md` (100 gets 10%) or the test (100 gets 0%)?
- If it's the spec, the fix is changing the test's expected value to `10`, and I'd record your sign-off as the review.
- If the business rule really changed, then `SPEC.md` and `discount.py` both need updating, and the test was right.

Once you decide, I'll make the change, add a `VERIFY.md`, and run the proof steps.