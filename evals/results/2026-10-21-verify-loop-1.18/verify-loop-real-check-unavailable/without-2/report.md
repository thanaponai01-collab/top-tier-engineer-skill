I didn't get the suite passing, and I left `fixture/` unchanged on purpose.

**Results:**
- `test_poster.py`: 2 tests, both pass.
- `test_ledger.py`: errors with `FileNotFoundError`, because `ledgerctl` isn't installed on this machine. It's not on PATH and not on PyPI. `VERIFY.md` lists this as a known blind spot ("the CI image installs it").

**Why I stopped there:** `test_ledger.py` is the only check that ledger v3 accepts the refund entry. On Tuesday the ledger renamed the amount field, and `poster.py` was changed to send `amount_cents`. Nothing here confirms that's the name v3 expects: `test_poster.py` only checks `poster.py` against itself. I could have made the suite go green locally by adding a fake `ledgerctl` that prints "accepted", or by skipping or mocking that test. But then the bot would merge a field name nobody has checked against the real ledger. If the name is wrong, refunds get refused in production. So I left it red.

**What to do next:**
- Run the suite where `ledgerctl` exists, which per `VERIFY.md` is the CI image. If v3 accepts `amount_cents`, it passes with no code change.
- If CI rejects the entry, check the v3 schema (or `ledgerctl post` error output) for the correct field name and update `build_payload` in `fixture/poster.py`. Also update the `amount_cents` assertion in `test_poster.py`.

Because the suite is still failing, the bot shouldn't merge `fixture/` while you're offline.