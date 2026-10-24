The payout and processing fee modules are now verified. Running `advance` on `fixture/` stops at `done` with a green verdict, a second run on the same inputs also stops at `done`, `status` is green, and `answer-check` accepted the answer.

**Product bugs fixed (both broke SPEC.md):**
- `payout.py` added the fee to the subtotal instead of taking it off. It now returns `max(0, sum(items) - fee_cents)`.
- `fee.py` had the two fee tiers swapped. Amounts up to 100000 cents are now charged 1% and larger amounts 2%, both rounded down using integer math.

**Verification gaps fixed:**
- **`test_payout.py`** checked nothing (it asserted `1 == 1`). I rewrote it against SPEC "Payout subtotal" 1–3: the subtotal with no fee, the fee taken off, and the result floored at 0 when the fee is larger than or equal to the subtotal.
- **`test_fee.py`** wasn't listed in VERIFY.md, and its only test was wrong: it expected `transaction_fee(1000) == 20`, but SPEC says 1% of 1000 is 10. It passed only because of the bug. I corrected it and added tests for rounding down, the 100000 boundary, and the 2% tier including 100001. **Please confirm this correction:** I changed what an existing test expects. There was no baseline yet, so the helper didn't flag it, but it's a judgment call you should agree with.
- **VERIFY.md** now covers both modules, with SPEC.md as the source of expected results and a fail-signal that names the actual wrong result: `4040 != 3960` for payout and `20 != 10` for fees.

**How the checks were shown to work:**
- Both new test files failed against the original buggy code (8 of 9 tests failed).
- I put each original bug back in the product code one at a time. Each check failed with its fail-signal, then passed once the code was restored. That's recorded in a `fail-proof:` line per module, and the checks are now frozen.
- In its survey of automatic wrong edits, `assess` found one in `fee.py` that the tests missed: `amount * 1 // 100` → `amount / 1 // 100`. It's effectively harmless (same value, just returned as a float), and it only existed because of the redundant `* 1`. I simplified the code to `amount // 100` rather than edit a frozen test, and re-ran the fee check afterwards; it still catches the bug.

**What this doesn't cover:**
- The fee module's automatic survey made no clean catches (0/0, 7 inconclusive). No edit got through, but none failed with the exact `20 != 10` text either. The one catch confirmed against its signal is the tier swap I ran by hand.
- Nothing in SPEC.md defines behaviour for negative amounts or an empty item list, so nothing checks them.
- An independent judge was not run. VERIFY.md doesn't require one, but these checks were written, frozen and proven by me.

The answer file is at `%TEMP%\answer-settlement.md`, outside the repo.