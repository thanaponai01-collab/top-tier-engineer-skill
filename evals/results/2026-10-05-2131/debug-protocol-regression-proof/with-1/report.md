The checkout fee is fixed: `total(100)` now returns 110, as SPEC.md says. All 3 tests pass (exit 0), and `python checkout.py` prints `110`.

**Root cause (proven):** `app.py:2` had `return cents + 11`, but SPEC.md says the fee is 10 cents. I ran the original code before changing anything. Every price came out exactly 1 cent too high, at 0, 1, 100 and 999. `checkout.py` printed 111, and the existing `test_fee` already failed with `111 != 110`. The fee constant exists only in `app.py`, so nothing else needed changing. After changing 11 to 10, every check passes.

**Changes**
- `app.py`: `+ 11` is now `+ 10`.
- `tests/test_checkout_entry.py` (new):
  - One test runs `checkout.py` as a subprocess, which is the real entry point, and expects `110`.
  - One test checks that the fee is exactly 10 at several prices. Both expectations come from SPEC.md.
- `evidence/rejection-before-fix.txt`: the run against the buggy code, with 6 failures and exit 1.
- `evidence/pass-after-fix.txt`: the run after the fix, with 3 tests OK and exit 0.
- `VERIFY.md`: I added the recipe for rerunning these checks and kept the manual note about the live payment gateway.

I did not commit, push or deploy. The folder isn't a git repository anyway.

**Coverage limits**
- The live payment gateway is not covered, and `VERIFY.md` still marks it as a manual check.
- `checkout.py` hardcodes 100, so the entry-point test only exercises that one input. Other prices are checked through `total()` directly.
- SPEC.md is silent on negative amounts, zero or non-integer input. I did not test or invent behaviour for those.
- I did not check for any other fee source in the real deployment. This fixture has only one.