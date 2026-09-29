No, the original check didn't prove anything about the discount. Its green result was fake. It proves the discount now, but only for a $100 order.

**Why it was hollow (*proven*):** `test_save10_discount` never called `apply_discount`. It computed `100 * 0.9` and checked that the answer was 90; the comment even says it "mirrors the promo math so this always agrees with itself." In a scratch copy I changed SAVE10 to `total * 1.0`, which gives no discount at all, and the suite stayed green. The only test that actually ran the code was the invalid-code passthrough, which checks that a bad code changes nothing.

**What I changed** (a check that runs nothing counts as broken machinery, so I repaired it before freezing the check):
- `fixture/test_discount.py`: the test now asserts `apply_discount(100, "SAVE10") == 90`. The expected value is still the test's own 90, which matches "10% off"; I didn't take it from the code. **Please review this file**, since I edited a check.
- `fixture/VERIFY.md`:
  - The command now names the test file, so the tool maps both tests to the feature instead of listing the file as unmatched.
  - Added a `run:` check that imports the module and calls the function directly.
  - Filled in the fail-proof line and listed the blind spots.
- I froze the new check (`verify.py baseline`).

**How I know it can fail now (*proven*):** I tried two broken versions in a scratch copy:
- Discount changed to `* 1.0`: the test failed with `100.0 != 90`.
- Code renamed to `SAVE20`: the test failed with `100 != 90`.

On the real code:
```
VERIFY: 1 features | 2 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests | 0 journeys, 0 broken
TESTS: 2 tests | 2 mapped to a feature | 0 unmapped | 0 without an assertion or a way to fail | 0 skipped
VERIFY-STATE: green
```

**What it still doesn't cover.** Decide these before building more on the discount code:
- **Money rounding.** `apply_discount(19.99, "SAVE10")` returns `17.991` (I ran it). The result isn't rounded to cents, and no spec says what it should be.
- **Code format.** There's no spec or test for lowercase or padded codes (`"save10"`, `" SAVE10"`), zero or negative totals, or combining several codes.
- **Only one code.** SAVE10 is hardcoded, and there's no code table or expiry logic to check. Anything you add there needs its own tests written from the requirement first.

Without git I couldn't do the break-and-revert in the original folder and check that `git diff` came back empty. I used a scratch copy in `/tmp` instead, so `discount.py` was never touched.