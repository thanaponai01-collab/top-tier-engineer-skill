# Billing

Small-business invoicing: create invoices, send them, correct them.

## Invariants
1. An invoice is immutable once sent. A correction is a credit note that references it; the sent
   invoice's lines and total never change.
2. Every sent invoice is emailed to the customer exactly once.

## Decisions
- 2026-08-12 · Corrections are credit notes, never edits: the accountant's audit requirement.
