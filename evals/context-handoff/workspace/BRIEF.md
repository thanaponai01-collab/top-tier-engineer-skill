# Goal
Help accounting export tenant invoices as JSON grouped per tenant.

## Invariants and acceptance criteria
1. JSON output is parseable; every exported invoice contains invoice_id and amount.
2. Tenants remain separated: input containing t1 and t2 produces distinct tenant groups; neither group contains the other tenant's invoices.
3. Preserve source identifiers for auditing; relevant area decisions remain current in the includes below.

## Decisions
- 2026-10-09 · Export JSON grouped per tenant, including invoice_id and amount, with tenants separated: accounting now requires this. Replaces CSV only (2026-10-09).

## Current area requirements
include: brief/auditing-0-19.md — read for auditing or source identifiers in areas 0–19.
include: brief/auditing-20-34.md — read for auditing or source identifiers in areas 20–34.

## Assumptions
- Tenant grouping representation | JSON object keyed by tenant_id, each value an invoice array | accounting may require a different envelope; confirm before depending on it externally.
- Empty input | empty JSON object | downstream may expect a different empty shape.
- Invalid or missing tenant_id, invoice_id, or amount | reject explicitly rather than silently dropping or mixing invoices | validation policy still needs agreement.

## Not building in this session
Exporter implementation, monthly wiring, live email delivery, and commits.

## Open questions
Exact JSON envelope and validation policy remain assumptions, not owner decisions.
Next implementation session should define a requirement-backed check (verify-loop), retain its rejection, then implement and prove the tenant-separated JSON behavior.
