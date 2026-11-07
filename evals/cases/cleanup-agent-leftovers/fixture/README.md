# budget

A small personal ledger.

    python budget.py list
    python budget.py add 12.50 Food 2026-03-01
    python budget.py report 2026-02
    python budget.py export csv|json|qif|ofx
    python budget.py import data/sample_import.csv
    python budget.py migrate

Tests: `python -m unittest discover tests`

## Upgrading an old ledger

Ledgers from before categories were required: run `python scripts/backfill.py` once, then
`python budget.py migrate`.
