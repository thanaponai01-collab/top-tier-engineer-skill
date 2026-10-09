# Build

proof line | status | commit
--- | --- | ---
`python -m unittest discover tests` → invoices load | proven | a1c09e2
`python cli.py export out.csv` → `exported 4 invoices` | proven | 5be7d31
`python -m unittest discover tests` → totals exact to the cent | proven | 9d04f6a

## Next
Slice 4: `python cli.py export OUT --month 2026-09` exports only that month's invoices (2 of 4).

## Deferred
what | why | trigger
--- | --- | ---
