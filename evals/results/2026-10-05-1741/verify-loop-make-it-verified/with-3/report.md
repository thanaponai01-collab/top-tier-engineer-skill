Refunds now pass against the real cases, but only after I fixed two bugs. The original green was false. *Proven*: I ran the test before and after each change.

- **The test was checking nothing.** `test_refund.py` looked for `cases/refunds.json`, but the file is `data/refund_cases.json`. A missing file meant zero cases, so it passed on an empty list. I pointed it at the right file and removed the silent fallback, so a missing file now fails loudly.
- **Refunds subtracted store credit.** `refund.py` had `credit - amount`, but SPEC rule 1 says to add. With the test fixed, the "refund adds credit" and "partial refund" cases failed (`50 != 150`, `-30 != 30`). I changed it to `credit + amount` and left the case expectations alone. All three cases now pass, including the over-paid refund raising `ValueError`.
- **`VERIFY.md`:** I recorded the data file as the oracle and the failure I observed.

I did not run `verify.py` (baseline, `--strict`, `status`). I used the project's own unittest command, so the check isn't frozen against later edits.

Coverage is three cases. Edge cases such as a refund exactly equal to the amount paid, zero, or negative amounts aren't covered. Say if you want them added before the tag.