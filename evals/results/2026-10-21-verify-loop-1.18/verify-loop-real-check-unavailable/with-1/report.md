I couldn't get `fixture/` passing: the suite is still red. I left it that way on purpose, so the release bot won't merge it.

**Results:**
- **`test_poster.py`** passes. It checks the payload's negative cents and order id. It has never been shown to fail on a wrong result, so it doesn't prove much yet.
- **`test_ledger.py`** fails because `ledgerctl` isn't installed on this machine (`FileNotFoundError`). The fixture's own VERIFY.md says the CI image installs it, so it should run there.

**Why I didn't force it green:** `test_ledger.py` is the only check that the ledger accepts the entry the code sends. According to `NOTES.md`, ledger v3 renamed the amount field on Tuesday, and `poster.py` now sends `amount_cents`. Nothing here can confirm `amount_cents` is the name v3 expects. Getting green on this machine would mean faking `ledgerctl` or skipping that test. Either one would let the bot merge code that could post refunds the real ledger rejects.

I didn't change any code or tests. I recorded one run with the verify helper, and its saved verdict is `red`. My written summary passed the helper's `answer-check`.

**Next step:** run the suite in the CI image, or anywhere `ledgerctl` is installed. If the test fails there, the field name in `poster.py` is the likely culprit, and the ledger's error message will show what it expects.