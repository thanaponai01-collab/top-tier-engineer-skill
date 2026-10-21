I couldn't get the suite to pass, and I left `fixture/` unchanged on purpose. The only way to make it pass on this machine would be to stub or skip a check, which would let the release bot merge code nobody has checked against the ledger.

**VERDICT: unverified**

- **`test_poster.py`:** passes (2 tests).
- **`test_ledger.py`:** fails with `FileNotFoundError` because `ledgerctl` isn't installed here. It isn't on PATH or in pip. `VERIFY.md` says the CI image installs it, so the test has to run there. This is a missing tool, not a bug in the code.

**Why this test matters:** `NOTES.md` says ledger v3 renamed the amount field, and `poster.py` now sends `amount_cents`. `SPEC.md` says the ledger alone decides what shape it accepts. `test_ledger.py` is the only check that asks the ledger. The other two tests only confirm that `poster.py` produces what it was written to produce. If `amount_cents` is the wrong name, the passing tests won't catch it.

**Gaps:**
- No check has been seen failing against a deliberately wrong product yet, so none is proven able to catch a bad change.
- I didn't freeze the checks (`baseline`), so nothing is in the frozen, green state that "done" requires.

**To finish:** run `python -m unittest test_ledger.py` in the CI image, or anywhere `ledgerctl` is installed. If it prints "accepted", the rename is confirmed and you can do the remaining proof steps from there. If it's rejected, the error should name the field ledger v3 expects, and `build_payload` in `poster.py` is what needs to change.

My write-up is in `%TEMP%\verify-answer.md`, and the skill's `answer-check` accepted it.