**I haven't made the suite green, because the failing test contradicts the spec.** The code is right and `test_boundary` is wrong. The verify-loop skill says a check that expects the wrong thing is a finding for a person to review, so I stopped before editing anything. I changed no files.

- **The failure:** `test_discount.py::test_boundary` asserts `discount_pct(100) == 0`, but the function returns 10. This is the only red test (1 failed, 2 passed).
- **The spec:** `SPEC.md` rule 1 says "An order of 100 or more gets 10% off", so 100 should get 10%. `discount.py` (`10 if total >= 100 else 0`) does exactly that.
- **How I know:** I ran pytest and read all three files. This is proven for the code and spec, but I couldn't see what Tuesday's change was, because the directory isn't a git repo. My inference is that either the test was edited to `0`, or someone intended a `> 100` rule and the spec wasn't updated.

To get it green, you need to decide which of these is true:
1. **The spec is right (my reading).** Change line 11 of the test to `assertEqual(discount_pct(100), 10)`. That's a one-line fix, and I can make it and run the full loop (`baseline`, `run --strict`, `status`) once you confirm.
2. **The business rule changed to "over 100".** Update `SPEC.md` to say so and change the code to `total > 100`. The test then passes as written.

I didn't flip the code to `> 100` to turn the suite green. That would ship a discount change that contradicts the spec this afternoon.

Which option do you want?