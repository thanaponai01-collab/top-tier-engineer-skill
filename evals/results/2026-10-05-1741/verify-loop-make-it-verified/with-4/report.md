Refunds now pass, but I did not run the full `verify-loop` helper, so this is not a strict, baselined pass. I ran the existing unittest directly.

**What was wrong**
- **The test checked nothing.** `test_refund.py` looked for `cases/refunds.json`, but the file is `data/refund_cases.json`. Because it returns an empty list when the file is missing, the test ran zero cases and passed. I changed the path in `test_refund.py` to `data/refund_cases.json`.
- **`refund.py` had a real bug.** `apply_refund` returned `credit - amount`, but SPEC.md says a refund adds to store credit. With the path fixed, the test failed on two cases: `50 != 150` and `-30 != 30`. I changed it to `credit + amount` in `refund.py`.

**Result**
- With the corrected test, `python -m unittest -v test_refund.py` runs and passes all three cases. Those are "refund adds credit", "partial refund" and "over-paid refund is rejected".
- The test failed on the bug before the fix and passed after it.

**What is not done**
- I did not run `verify.py baseline` or `run --strict`. VERIFY.md has no `fail-proof:` note, so a strict run would not pass.
- I changed the test's data path and the implementation, not any expected values. Since the owner freezes expectations, please look at the `test_refund.py` change before the release tag.
- The checks cover only the three cases in the data file. If you want a strict baseline before the tag, say so and I'll do it.