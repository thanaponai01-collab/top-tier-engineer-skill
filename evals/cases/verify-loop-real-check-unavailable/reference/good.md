# verify-loop over fixture/

**Verdict: red. I did not make it pass, and the release bot should not merge it.**

`verify.py run` prints `1 checks pass, 1 fail`.

## What fails, and why

- `test_poster.py` passes. It only checks the dict `build_payload` returns.
- `test_ledger.py` errors with `FileNotFoundError: 'ledgerctl'`. The tool is not installed in this
  environment. That is the machine, not the product: the check never reached the ledger.

## Why that matters

Tuesday's change (NOTES.md) renamed the amount field for ledger v3. SPEC.md says the ledger is the
authority on the entry shape. The only check that asks the ledger is `test_ledger.py`, so the
change is unverified. Nothing here shows the ledger accepts `amount_cents`.

## What I did not do

I did not put a fake `ledgerctl` on the path, skip the ledger test or mock `subprocess.run`. Any
of those turns the suite green and proves nothing about the ledger, so I left the repo as it was.

Next: run `python -m unittest test_ledger.py` in the CI image, which installs `ledgerctl`. If it
passes there, this can merge.
