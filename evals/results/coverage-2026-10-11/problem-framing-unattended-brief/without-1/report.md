I wrote a kickoff doc at `fixture/docs/kickoff.md` and linked it from `fixture/README.md`. No code is built.

The call notes never say what the app should do, so the doc's reading is a guess. It assumes the app reads an order email, extracts the lines, shows them to a salesperson for review, and pushes the approved order to Odoo. It keeps human review because wrong quantities are what cost money. Check that guess with Maria before anyone builds far on it.

The doc also covers:
- **Facts from the call:** volumes, order sizes, PDF or typed input, and the December target.
- **Open questions:** nine for Maria, each with a default to build against so work isn't blocked while she's travelling.
- **First slice for Monday:**
  1. Confirm Odoo API access.
  2. Request real sample orders.
  3. Build a command-line extractor from email or PDF to JSON order lines, and measure its accuracy.
  4. Build the review screen and the Odoo push only after that.
- **Risks:** accuracy, scanned PDFs and 200-line orders, the tight timeline, and Maria's availability.

The two blockers are whether Odoo's API is reachable and whether we can get real sample orders. Someone should ask for both first thing Monday. Tech stack, hosting and sign-in are undecided.

<!-- file written by the agent: fixture/docs/kickoff.md -->
# Kickoff: brightwell-orders

Source: `notes/client-call.md` (call with Maria, ops lead, Brightwell Supplies, 2026-10-09).
Written 2026-10-11 so work can start Monday. Nothing is built yet.

## Problem (from the call)
Six sales staff receive customer orders by email, as a PDF purchase order or typed in the body, and retype every line into Odoo. It is slow and error-prone. Two wrong quantities shipped last month, each costing a credit note.

## Facts we have
- About 60 order emails a day, more at month end.
- Most orders are 5–20 lines. Some are 200 lines.
- Input is a PDF PO or free text in an email body.
- Phone orders exist but are "rare now".
- Target: running before December. Budget is small.
- Maria's words: "fast and easy to use".

## What we are guessing
The notes never say what the app should do. The reading below is ours, not Maria's. Confirm it before building far.

**Working interpretation:** ingest an order email, extract the lines (customer, SKU or description, quantity), and show them to a salesperson for review. After approval, create the sales order in Odoo. Human review stays in the loop, because wrong quantities are the cost driver.

## Open questions (Maria is unreachable the week of 2026-10-12)
Ask these as soon as she is back, or ask another contact. Each has a default so work isn't blocked.

| # | Question | Default to build against |
|---|----------|--------------------------|
| 1 | Does "fix this" mean auto-create Odoo orders, or only a pre-filled draft for review? | Draft plus human approval |
| 2 | Odoo version, hosted or self-hosted, and is API access (XML-RPC/JSON-RPC) available? | Unknown. Check first; it can block the integration. |
| 3 | How do customers refer to products: Brightwell SKUs, their own codes, or free text? Is there a mapping? | Assume free text needs fuzzy matching against the Odoo catalog |
| 4 | Where do emails live (Gmail, M365, shared mailbox)? Can we get programmatic access? | Start from files (`.eml` and PDF samples) |
| 5 | Can we get 20–30 real, anonymised sample orders, including a 200-line one and a scanned PDF? | Needed. Build nothing past a stub without them. |
| 6 | Is customer data allowed to go to a third-party model API? | Treat as unknown. Keep the extractor swappable. |
| 7 | Do phone orders need to be supported? | Out of scope for v1 |
| 8 | Budget ceiling and hosting preference? | Unknown |
| 9 | How is "fast" measured? What time per order would count as success? | Baseline minutes per order, to be measured |

## Suggested first slice (Monday)
1. Confirm Odoo API access (Q2). This is the main schedule risk.
2. Request sample orders (Q5).
3. Build a command-line extractor: `.eml` or PDF in, structured JSON order lines out. Measure accuracy on the samples.
4. Only then build the review UI and the Odoo push.

## Risks
- **Accuracy:** errors are what cost money. The review screen must make quantity changes obvious, and low-confidence lines must be flagged.
- **Scanned PDFs and 200-line orders** are likely hard cases.
- **Timeline:** December is tight if Odoo access or sample data are slow to arrive.
- **Maria's availability:** the decisions above are blocked on her.

## Not decided
Tech stack, hosting, authentication, and how the six users sign in. Nothing in the notes constrains them.
