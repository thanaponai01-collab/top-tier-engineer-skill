`fixture/` refunds are verified: `run --strict` passes and `status` prints `VERIFY-STATE: green`. That needed two fixes, one to the check and one to the product code.

**The check was empty.** `test_refund.py` read `cases/refunds.json`, but the data is at `data/refund_cases.json`. A missing file silently returned `[]`, so the test passed with zero cases. I repaired it in three ways:
- It now points at the real file.
- It fails if no cases load.
- I did not change any expected values.

**The product bug.** `refund.py` returned `credit - amount`, which breaks SPEC rule 1 (a refund adds to store credit). It now returns `credit + amount`.

**Evidence:**
- With the repaired check on the buggy code, it failed with `AssertionError: -30 != 30` (the "partial refund" case). It also failed one more case, which I didn't read.
- After the fix it passes, and `verify.py tests --strict` shows 1 test mapped, none unable to fail.
- `VERIFY.md` now has the oracle files (`SPEC.md`, `data/refund_cases.json`), the fail-signal and a fail-proof note, and the baseline is frozen.

**Gaps to know before tagging:**
- The `-30 != 30` signal is the case I actually saw fail. I changed it from an earlier guess (`50 != 150`) after the first negative run, so the final signal was never matched on a fresh failing run before the fix. `run --strict` still accepted the receipt, but a person may want to look at that.
- SPEC rule 2 (a refund larger than the amount paid raises `ValueError`) is covered by one case and already passed before the fix.
- Only `data/refund_cases.json` is covered. Nothing else was mapped, and the blind spots section is empty.
- There is no git here, so I couldn't confirm a clean diff after restoring the bug. I fixed the code directly instead.

Please review the edits to `test_refund.py` and `VERIFY.md` before the release tag.