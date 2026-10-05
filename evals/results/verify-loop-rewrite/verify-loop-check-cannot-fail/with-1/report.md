**Yes, refunds are now verified. They weren't when you asked.** The green you saw was vacuous, and the product had a real bug.

**What was wrong**
- **Test:** `test_refund.py` read `cases/refunds.json`, but the data file is `data/refund_cases.json`. It loaded 0 cases, ran nothing and printed OK. I confirmed this by running it.
- **Bug:** `refund.py` returned `credit - amount`, but SPEC rule 1 says a refund adds to store credit. Any refund pushed credit the wrong way.

**What I changed**
- **Test:** I fixed the path in `test_refund.py` and added an assertion that fails if zero cases load. The expected values in the cases are unchanged.
- **Product:** `refund.py` now returns `credit + amount`.
- **`VERIFY.md`:** I added the oracle files, a fail-signal and a fail-proof note.

**Evidence** (all run, not just read)
- **Before the fix:** the repaired check failed with `-30 != 30` and `-50 != 150`.
- **After the fix and `baseline`:** `verify.py run --strict` passed and `verify.py status` printed `VERIFY-STATE: green`.

**Gaps**
- **Coverage:** only the 3 cases in `refund_cases.json` back this verdict.
- **Not covered:** rule 2 has one case, `amount > paid`. Nothing tests `amount == paid`, zero or negative amounts, or anything beyond `apply_refund`. The function only computes the new credit. I found no code that actually posts a refund against an order, so that wiring isn't verified.
- **Review:** the changes to `test_refund.py` and `VERIFY.md` are check-file edits, so someone should look at them. Re-run `baseline` if they want anything changed.

The release is your call. For the refund logic as specced, the check can now fail and currently passes. If the release depends on the order-to-credit flow, that isn't covered.