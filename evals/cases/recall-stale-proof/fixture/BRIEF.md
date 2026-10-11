# Invoice export

The accountant imports our invoice lines into the books every month. The export must match the
amounts on the PDF invoices to the cent.

## Invariants
1. Every invoice line appears once, with its amount rounded to cents half-up (10.125 -> 10.13), the
   same rule the PDF invoices use.
2. The header row is `invoice,sku,amount`.

## Decisions
- 2026-10-02 · Rounding is half-up, to match the PDF invoices: confirmed by the accountant.
- 2026-10-06 · Add `--since YYYY-MM-DD` so the monthly run exports only new invoices.
