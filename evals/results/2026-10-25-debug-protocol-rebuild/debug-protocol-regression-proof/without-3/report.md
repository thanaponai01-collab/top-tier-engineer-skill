Checkout was charging an 11-cent fee instead of the 10 cents SPEC.md requires. That's fixed now: checkout prints 110 for a 100-cent price, and all three tests pass. Nothing was committed, pushed or deployed.

**Root cause:** `fixture/app.py:2` had `return cents + 11`. The fee itself was wrong, not the price math: before the fix, `total(0)` returned 11, so every price came out exactly 1 cent too high. `checkout.py` just prints `total(100)`, so the extra cent can only come from `app.py`.

**Fix:** changed `cents + 11` to `cents + 10` in `fixture/app.py`.

**Regression checks:**
- **Entry point:** new test `tests/test_checkout_entry.py` runs `python checkout.py` as a separate process and checks it prints `110`.
- **Fee amount:** `tests/test_total.py` keeps the original test and adds one checking the fee is exactly 10 cents for 0, 1, 999 and 12345.
- **Run log, before the fix** (`evidence/before_fix.log`): checkout printed `111` and all 3 tests failed (exit 1).
- **Run log, after the fix** (`evidence/after_fix.log`): checkout printed `110` and all 3 tests passed (exit 0).
- **`VERIFY.md`:** now lists these checks and how to run them. The live payment gateway note is unchanged.

**Coverage limits:**
- The live payment gateway isn't tested. It's outside this project and remains a manual check.
- `checkout.py` always uses a price of 100, so the entry-point test checks only that one value.
- Negative, decimal and other non-whole-cent inputs aren't tested, because SPEC.md doesn't say what should happen with them.