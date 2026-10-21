## Refund posting
- path: poster.py
- test: `python -m unittest test_poster.py`
- test: `python -m unittest test_ledger.py`
- oracle: SPEC.md

## Blind spots
- test_ledger.py needs `ledgerctl` on PATH; the CI image installs it.
