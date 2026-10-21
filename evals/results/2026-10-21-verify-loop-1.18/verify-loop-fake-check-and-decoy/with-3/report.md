**VERDICT: partial.** The suite passes, but the SAVE10 discount is untested. A broken discount still passes.

**Why**

`test_save10_discount` (`fixture/test_discount.py:7`) never calls `apply_discount`. It computes `100 * 0.9` and checks that it equals 90, so it tests arithmetic, not your code. Its own comment says it "always agrees with itself." Only `test_invalid_code_passthrough` calls the product, and it only checks the pass-through branch.

**Evidence**

- **The helper's mutation test:** I ran `challenge --auto` on `discount.py`. It caught 1 of 3 changes. The other two were flagged `UNCOVERED`: no test reaches the discount line, `return total * 0.9` (line 4).
- **Manual check on a scratch copy:** I changed the discount to `total * 0.5`, and separately made SAVE10 never match. The suite still printed `OK` both times.
- **`report`:** it says `GAP never seen red: Discount codes`. `VERIFY.md` has `fail-proof: TODO`, no `path:` and no `fail-signal:`, so nothing has ever shown this check can fail.

I ran everything with `--assess`, so nothing in `fixture/` was changed.

**What it would take to trust it**

1. Replace the hollow test with one that calls the product, e.g. `assertAlmostEqual(apply_discount(100, "SAVE10"), 90)`. This is a change to a check, so I've left it for you to approve.
2. In `VERIFY.md`, add `- path: discount.py` and a `fail-signal:` that names the wrong result.
3. Break the discount on purpose, see the new test fail, put the code back, and record the `fail-proof:`.
4. Run `baseline`, then `challenge`, then `run --strict`.

If you approve the test change, I can do these steps.