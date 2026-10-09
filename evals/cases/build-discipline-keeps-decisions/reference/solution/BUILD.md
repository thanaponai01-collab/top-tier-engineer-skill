# Build

proof line | status | commit
--- | --- | ---
`python -m unittest discover tests` → invoices load | proven | a1c09e2
`python cli.py export out.csv` → `exported 4 invoices` | proven | 5be7d31
`python -m unittest discover tests` → totals exact to the cent | proven | 9d04f6a
`python cli.py export out.json --month 2026-09` → JSON with INV-103, INV-104 | proven | uncommitted

## Next
Nothing planned; ask.

## Deferred
what | why | trigger
--- | --- | ---
