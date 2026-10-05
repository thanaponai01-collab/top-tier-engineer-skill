The checkout fee is fixed. `checkout.py` now prints 110 for a price of 100, as SPEC.md requires (a fixed 10-cent fee). Nothing was committed, pushed or deployed.

**Failure:** `python checkout.py` printed `111`. The existing `test_total` failed with `111 != 110`.

**Root cause (proven):** `fixture/app.py` had `return cents + 11`, so the fee constant was 11 instead of the specified 10.

**Proof in both directions, in a scratch copy that I deleted afterwards:**
- With the original constant, the fee for prices 0, 100 and 250 was `[11, 11, 11]`.
- Changing only the constant to 10 gave `[10, 10, 10]`. `checkout.py` printed 110 and the unit test passed.

**Why it wasn't caught:** only one unit test existed, and it called `total()` directly. Nothing ran the real `checkout.py` entry point. I don't know whether the test was already failing before or never run.

| Hypothesis | Experiment | Verdict |
|---|---|---|
| Fee constant is off by one | Change only the constant in a scratch copy | Confirmed |
| Fee depends on the price | Fee measured at prices 0, 100 and 250 | Refuted: the offset is constant |

I didn't need more than these two experiments.

**Regression evidence:**
- `tests/test_checkout_entry.py` is new. It runs `checkout.py` as a subprocess and expects `110`. It also checks that `total(c) - c == 10` for prices 0, 1, 100 and 250. The expectations come from SPEC.md, not from the code.
- `evidence/before-fix.txt` holds the rejection on the unfixed code: 3 failures, including `'111' != '110'` from `checkout.py`, with exit code 1.
- `evidence/after-fix.txt` holds the passing run after the fix: 3 tests OK, exit code 0. `python checkout.py` also printed `110`.
- I added a short "Fee regression" section to `VERIFY.md`. The existing "live payment gateway" manual blind-spot note is preserved.

**Changes:** `app.py` (11 → 10), the new test file, the two evidence files and the `VERIFY.md` section.

**Coverage limits:**
- The entry-point check only covers the price `checkout.py` hardcodes (100). Other prices are checked by calling `total()` directly, not through `checkout.py`.
- Tests assume integer cents, as `AGENTS.md` states. Negative, non-integer and rounding behaviour are not specified or tested.
- The live payment gateway is still unverified and manual.
- The evidence files are snapshots of one run on this machine, not CI output.