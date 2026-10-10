Wrote `BRIEF.md`. Costliest assumption, first: **orders land in Odoo as draft sales orders a
salesperson confirms. Nothing is posted automatically.** If Maria wants straight-through posting,
the error tolerance below has to tighten a lot.

**Job:** sales staff stop retyping emailed orders into Odoo, and quantity typos stop reaching
shipments (two double shipments and credit notes last month).

**Who touches it:** 6 salespeople (review drafts), customers (send email/PDF as today; nothing new for
them), Odoo (receives draft orders via its API).

**Invariants → acceptance criteria**
1. No order reaches Odoo without a person confirming it → every order created has state `draft`
   until a user clicks confirm (check: Odoo audit log).
2. Quantities are never silently guessed → any line parsed with confidence below the threshold, or
   with an unknown SKU, is flagged and blocks confirm until a person fixes it.
3. A 20-line emailed order is ready for review in under 60 s from arrival, and a 200-line PDF in
   under 5 minutes (assumed: text PDFs, not scans).
4. Review of a 20-line order takes a salesperson under 2 minutes, measured on 10 real past orders,
   versus today's retyping time (to be timed on Monday).
5. If Odoo is unavailable the draft is kept and retried, and the salesperson sees "not yet in Odoo".
   Nothing is lost.

**Not building:** phone orders; changes for customers; auto-posting; a customer portal.

**Assumptions** | default | cost if wrong
- Drafts, not auto-post | drafts | high: redesign confirm flow
- PDFs are text | text | medium: needs OCR
- One shared inbox | yes | low

**Open question for Maria (one):** may confirmed orders ever post without a human?

Next: turn criteria 1–5 into the exit check (`verify-loop`).
