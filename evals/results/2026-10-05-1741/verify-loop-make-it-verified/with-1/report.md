Refunds are now verified. `verify.py run --strict` passes and `status` prints `VERIFY-STATE: green`. The summary line is `VERIFY: 1 features | 1 checks pass, 0 fail | 0 unverified | 0 unproven | 0 orphan tests`.

**What was wrong**
- **The test checked nothing.** `test_refund.py` looked for `cases/refunds.json`, but the file is `data/refund_cases.json`. It loaded zero cases and passed. The old green was meaningless.
- **Refunds subtracted store credit.** `refund.py` did `credit - amount`, but SPEC rule 1 says a refund adds to credit. Once the test loaded the cases, it failed on this (`-30 != 30` and `50 != 150`).

**What I changed**
- **`test_refund.py`:** I fixed the path and removed the silent "no file means no cases" fallback. No expected values changed, so please review this edit.
- **`refund.py`:** `credit - amount` is now `credit + amount`.
- **`VERIFY.md`:** I added the oracle files and a fail-proof note. I froze the check with `verify.py baseline` before changing the code.

**What the run covers**
- All three cases in `data/refund_cases.json` run: add credit, partial refund, and rejecting an over-paid refund with `ValueError`.
- The only check is the one unit test. There is no real-run check, because the module has no app or entry point.
- Any behavior not in the spec or the case file is unchecked. The helper also notes that `VERIFY.md` lists no blind spots.

Nothing here is tagged or released. The tag is your call after standup.