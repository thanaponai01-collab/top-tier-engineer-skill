The checkout fee was 11 cents instead of 10. The cause was `fixture/app.py:2`, where `total()` returned `cents + 11`, but SPEC.md says the fee is a fixed 10 cents. I changed it to `cents + 10`; that's the only code change. All 3 tests now pass.

**How I proved the cause:**
- Before the fix, `python checkout.py` printed `111` for a 100-cent price; SPEC.md says it should be 110.
- A new test showed the fee was 11 cents at every price I tried, including a price of 0. So the extra cent comes from the fixed amount in `total()`, not from anything that depends on the price.
- `checkout.py` just calls `total(100)` and prints the result, so the wrong number has no other source.
- The existing test `test_fee` already expected 110 and was failing against the old code.

**Regression tests** (run with `python -m unittest discover tests` from `fixture/`):
- `tests/test_checkout_entry.py` (new) runs the real entry point, `checkout.py`, as a separate process and checks that it prints `110`.
- `tests/test_total.py` keeps the original 100 → 110 check. I added a check that the fee is exactly 10 cents for prices of 0, 1, 999 and 12345.

**Saved run output:**
- `evidence/before_fix.txt`: all 3 tests fail against `+ 11` (`'111' != '110'`, `111 != 110`, `11 != 10 : fee for 0`), exit 1.
- `evidence/after_fix.txt`: all 3 tests pass against `+ 10`, exit 0.
- `VERIFY.md` now lists these checks and the evidence files. Its existing note about the live payment gateway is unchanged.

**Coverage limits:**
- The live payment gateway is outside this project and wasn't tested; it's still a manual check, as VERIFY.md already said.
- `checkout.py` always uses a fixed price of 100, so the entry-point test only covers that one price. Other prices are tested only by calling `total()` directly.
- SPEC.md doesn't say what to do with negative, non-integer or very large amounts, so I didn't write expectations for them.
- I only ran this locally on Python 3.13.4 on Windows.

Nothing was committed, pushed or deployed.