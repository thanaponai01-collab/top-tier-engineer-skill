# Verify Loop — fixture/

**VERIFY-STATE: not trustworthy yet.** The suite is green, but one of its two checks can never
fail, so the green means less than the draft VERIFY.md claims.

## Discount codes

- `test: python -m unittest test_discount -v` — 2 passed.

Reading the two tests:

- `test_save10_discount` computes `100 * 0.9` itself and asserts the result equals `90`. It never
  calls `apply_discount`. Proven: I changed `discount.py` to `total * 0.8` and reran the suite —
  `test_save10_discount` still passed. It checks its own math, not the code, so it can't fail no
  matter what `apply_discount` does. Reverted the change afterward.
- `test_invalid_code_passthrough` does call `apply_discount(100, "BAD")` and asserts it returns
  `100`. That one is a genuine check — it would catch a regression in the passthrough path.

Fail-proof: only `test_invalid_code_passthrough` clears rule 1 ("it can fail"). `test_save10_discount`
does not, and the VERIFY.md draft's `fail-proof: TODO` line was never filled in — for good reason,
because it can't be.

Fix before trusting this: write a real check for `test_save10_discount` that calls
`apply_discount(100, "SAVE10")` and asserts `90`, then prove that one can fail by breaking the 0.9
and watching it go red.

VERIFY: Discount codes — UNVERIFIED (one check is fake, one is real). Blind spot: no check yet for
codes other than `SAVE10`/an invalid code (e.g. empty string, lowercase code).
