I've written a project brief for Monday. I haven't built any code, because the call notes don't say enough to build on yet.

The brief is `fixture/docs/brief.md`, and I updated `fixture/README.md` to point to it. The brief covers:
- **The problem and the facts from the call:** volumes, order sizes, the typo cost, and the December target.
- **Assumptions I made, marked as unconfirmed:**
  - The tool should extract order lines and create a draft Odoo order for a person to review before submitting.
  - Phone orders are out of scope for version 1.
  - Matching customers' product names to Odoo products is probably the hardest part.
- **Nine open questions for Maria**, to send in one batch:
  - Which Odoo version and hosting they have, and whether we can get API access.
  - Sample order emails and PDFs, including a 200-line one.
  - How customers identify products.
  - Whether order content can go to a third-party service, such as an LLM API.
- **Suggested first steps and risks** for Monday.

I didn't contact Maria or anyone else. The most urgent questions are Odoo access, sample orders and the third-party-service question, because Maria is hard to reach next week and the December deadline is tight.

<!-- file written by the agent: fixture/docs/brief.md -->
# Brightwell order entry: project brief

Source: call with Maria (ops lead, Brightwell Supplies), 2026-10-09. See `notes/client-call.md`.
Status: pre-build. Nothing has been confirmed beyond the call notes. Everything under "Assumptions" is ours, not the client's.

## Problem

Six sales staff receive customer orders by email, either as a PDF purchase order or typed in the email body. They retype every line into Odoo (their ERP). This is slow and error-prone. Last month typos caused wrong quantities to ship twice, and each time a credit note was issued.

## What the client asked for

"An app that fixes this. It has to be fast and easy to use."

## Facts from the call

- Users: 6 sales staff.
- Volume: about 60 order emails/day, more at month end.
- Order size: most 5–20 lines, some up to 200.
- Input formats: PDF purchase order, or plain text in the email body.
- Phone orders exist but are "rare now".
- Target: running before the busy season (December). Budget is small.
- Maria is travelling the week of 2026-10-12 and hard to reach.

## Assumptions (unconfirmed, verify before relying on them)

1. The goal is to extract order lines from the email or PDF and create (or pre-fill) a draft sales order in Odoo, with a human reviewing before confirming. Nothing in the notes says it should be fully automatic. Given the cost of a wrong quantity, review-before-submit is the safer default.
2. Phone orders are out of scope for v1.
3. Customers' product codes or descriptions need matching to Odoo products. This is probably the hardest part and the call didn't discuss it.

## Open questions for Maria

These block design decisions. Ask them in one batch.

1. Odoo: which version, hosted (Odoo.sh, Odoo Online) or self-hosted, and can we get API access (and a test database)? Online plans may restrict external API use.
2. Who creates the order today: a draft quotation or a confirmed sales order? Is there an approval step?
3. How do customers identify products: Brightwell SKUs, their own codes, or free-text descriptions? Is there a mapping today?
4. Sample data: 10–20 real order emails and PDFs (anonymised is fine), including a 200-line one and a messy one.
5. Are the PDFs text-based or scanned? Do the layouts vary by customer?
6. Where do orders arrive: shared inbox or each person's mailbox? Which mail system (Microsoft 365, Google Workspace, other)?
7. "Fast and easy": what does a successful outcome look like (for example, time per order, error count)? What is the current time per order?
8. Budget figure and the hard deadline within December.
9. Data handling: can order content go to a third-party service (for example, an LLM API)? This affects the whole architecture.

## Suggested first steps for Monday

1. Send the open questions to Maria (she is hard to reach, so email rather than waiting for a call). Questions 1, 4 and 9 are the most urgent.
2. While waiting, prototype extraction only on whatever sample orders can be obtained, or on synthetic ones. Don't build Odoo integration or UI before answers to Q1–Q3.
3. Decide the approach once Q9 is answered: LLM-based extraction vs. rule/template parsing.
4. Agree a v1 scope with Maria: likely "paste or upload an order, review extracted lines, push to Odoo as a draft".

## Risks

- December deadline with a small budget and no sample data yet. Scope must stay small.
- Product matching accuracy decides whether this saves time or merely moves the typing to correcting.
- Extraction mistakes could reintroduce the same errors the client is paying to remove, so the review step matters.
