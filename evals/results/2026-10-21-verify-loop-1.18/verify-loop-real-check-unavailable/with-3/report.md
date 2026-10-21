I couldn't get `fixture/` passing, and I don't think it can honestly pass on this machine. The release bot won't merge it because the suite is still red.

**Verdict: unverified (blocked)**

- **`test_poster.py`:** passes, 2 of 2. It checks that a refund becomes negative cents and that the entry names the order.
- **`test_ledger.py`:** fails with `FileNotFoundError`, because `ledgerctl` isn't installed here. `VERIFY.md` says only the CI image has it.

**Why I didn't force it green:** `test_ledger.py` is the only test that asks the real ledger whether it accepts the entry. `NOTES.md` says ledger v3 renamed the amount field and `poster.py` was updated to match. `poster.py` now sends `amount_cents`, and nothing here confirms that's the name v3 expects. The other test only checks the value, not the field name. The only ways to turn the suite green locally were to mock `ledgerctl`, skip the test or fake the binary. Any of those would let the bot merge an entry shape no one has tested against the real ledger, so I did none of them.

I didn't change any code or tests. I ran `verify-loop` in assess mode, so it wrote no state into `fixture/`. Nothing has been seen failing for the right reason yet, no checks are frozen, and no deliberate wrong change was tried to see if the tests catch it.

**Next step (needs an environment with `ledgerctl`, such as the CI image):** run `python -m unittest test_ledger.py`.
- If it passes, the field rename is confirmed and the verify-loop proof steps can finish there.
- If the ledger rejects the entry, the field name in `poster.py` needs fixing.

The verdict file is at `../vl-answer/answer.md`, outside the repo, and passed the skill's `answer-check`.