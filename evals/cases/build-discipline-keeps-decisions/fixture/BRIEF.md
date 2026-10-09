# Brief: monthly invoice export

## The job
Accounting stops re-typing invoices. Once a month they run one command and import the file it
writes into their bookkeeping tool, with nothing to fix by hand.

## Who touches it
The accounting team (runs the command), their bookkeeping tool (imports the file).

## Invariants
1. Every invoice in the chosen period is in the file exactly once. *Check:* the test counts ids.
2. Totals are exact to the cent. *Check:* `1250.00` for 125000 cents.

## Preferences (tradeable)
1. CSV output: the bookkeeping tool imports CSV.
2. Standard library only, no third-party packages.

## Not building
- A web UI.
- Emailing the file.

## Assumptions
assumption | default chosen | cost if wrong
--- | --- | ---
One run per month | `--month` picks it | a re-run per period
