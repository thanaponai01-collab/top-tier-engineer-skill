I wrote the problem brief to `fixture/BRIEF.md` and added a "start here" line to `fixture/README.md` pointing to it. Nothing is built, and I didn't ask any questions since you and Maria are off. Every unknown is taken at the likeliest reading and marked *assumed* in the brief.

**What the brief says:** six sales staff stop retyping emailed orders (PDF or typed in the body) into Odoo. Each email becomes a draft Odoo order that a person checks and confirms. That targets the typos that caused two wrong shipments and two credit notes last month.

**Costliest assumption:** that we can create orders in Odoo through its API. We don't know the version, whether it's hosted or self-hosted, or whether we can get API credentials. If that's wrong, the design changes.

**Other assumptions I took:**
- **Human review:** staff confirm every order. The app never confirms one itself.
- **Thresholds:** accuracy, review time and month-end peak (about 3x, so roughly 180 emails a day) are my guesses, since the call only said "fast and easy". Maria needs to agree to them.
- **Not building:** auto-confirm, a customer portal, Excel or image attachments, and phone-order capture beyond a cheap form. Phone orders were called rare.

The brief has six acceptance criteria that a person who never read the code could check. They cover unflagged wrong quantities, nothing lost or duplicated, safe failure when Odoo is down, review time, and volume. It also covers 200-line orders.

**For Monday:** two questions block the build, and Maria is travelling and hard to reach, so send them in writing:
1. Which Odoo version and hosting, and can we get an API user?
2. Can she send 30 or more real past order emails with the orders as entered in Odoo? I need those to test accuracy.

Four more open questions are in the brief:
- How customers identify products.
- Whether orders come into one shared inbox or six.
- What "small" budget means, and whether December is a hard date.
- Whether sending order emails to an AI extraction service is acceptable.

After that, `verify-loop` can turn the acceptance criteria into the exit check, and `plan-work` can cut the slices. I'd hold off on design until the Odoo access and the sample emails are in.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief: brightwell-orders

Framed 2026-10-11 from `notes/client-call.md` (call with Maria, ops lead, 2026-10-09). Nobody was reachable
to ask, so every unknown below is taken at the likeliest reading and marked *assumed*.

**Costliest assumption:** we can create orders in Odoo through its API (version, hosting and credentials are
unknown). If Odoo can't be written to, the whole design changes (see Open questions, #1).

## 1. The job

Six sales staff stop retyping emailed customer orders into Odoo line by line. After this ships, an order
email (PDF purchase order or typed in the body) becomes a **draft** Odoo sales order that a person checks and
confirms. The retyping typos that caused two wrong-quantity shipments and two credit notes last month can no
longer enter silently.

## 2. Who touches it

- Six sales staff: review and confirm drafts. Not technical.
- Customers: send emails; they don't use the app and their formats vary.
- Odoo (ERP): receives orders.
- Maria: owner and decision-maker; hard to reach the week of 2026-10-12.

## 3. Invariants (each with a check)

1. **No silent errors.** Nothing reaches a confirmed Odoo order without a human having seen every line next
   to the source text. *Check:* the app has no code path that confirms an order; drafts only. (*assumed*, see A1)
2. **Extraction is faithful.** Quantities and product identifiers in the draft match the source. *Check:* on a
   test set of at least 30 real past emails (PDF and body-text, including 3+ orders of 200 lines), every line's
   quantity is correct in at least 99% of lines, and every wrong or uncertain line is flagged for review. The
   target is no unflagged wrong quantity. (*assumed* threshold; Maria to agree)
3. **Nothing is lost or duplicated.** Every order email ends as exactly one draft or one visible "needs manual
   handling" item. *Check:* feed 60 emails, including a re-delivered duplicate: 60 outcomes, no dupes, no
   drops.
4. **Failure is visible and safe.** Unreadable PDF, unknown customer, unmatched product, or Odoo being down
   produces a flagged item with a reason, never a guessed value or a crash. *Check:* one test per case, each
   asserting a flagged item and an unchanged Odoo.
5. **Saves time.** A typical 5–20 line order takes the reviewer less than 2 minutes from opening the draft to
   confirming, measured with 2 staff on 10 real orders, against a baseline timed first. (*assumed* target; "fast
   and easy" was the only thing said)
6. **Volume.** Handles 60 emails/day, with month-end peaks assumed at 3x (180/day), and a 200-line order is
   processed in under 2 minutes. (*assumed* peak)

## 4. Preferences (tradeable)

1. Phone orders: a manual entry form in the same review screen, if cheap.
2. Reviewer sees the source email or PDF beside the draft.
3. Corrections feed back (remember "ACME's 'bolt M8' is SKU 1234").
4. Small budget: prefer hosted/off-the-shelf parts over bespoke infrastructure.

## 5. Not building

- Auto-confirming orders without review.
- Replacing or customising Odoo itself.
- A customer-facing portal or order form.
- Pricing, stock or credit checks beyond what Odoo already does on a draft.
- Phone-order capture beyond preference 1 ("rare now").
- Handling attachments other than PDF and plain/HTML email body (e.g. Excel, images) in v1; these are flagged
  per invariant 4.

## 6. Open questions for Maria (answer order = impact)

1. **Odoo:** which version, cloud (Odoo Online/Odoo.sh) or self-hosted, and can we get an API user? Owner of
   the answer: Maria or their Odoo admin. Blocks any build; first Monday task.
2. **Samples:** 30+ real past order emails (anonymised if needed) with the orders as entered in Odoo. Needed
   for invariant 2; also tells us how messy the formats are.
3. **Product matching:** do customers use Brightwell SKUs, their own codes or free-text descriptions? Is there
   a customer-to-product mapping anywhere?
4. **Mailbox:** one shared orders inbox, or each of six staff receives separately? Can we get forwarding or
   IMAP/Graph access?
5. **Budget and December:** what does "small" mean in numbers, and is December a hard date or a hope? If hard,
   what is the minimum (e.g. body-text emails only) acceptable by then?
6. **Data handling:** customer order emails would be sent to an AI/extraction service. Is that acceptable to
   Brightwell and their customers?

## 7. Assumptions

| assumption | default chosen | cost if wrong |
|---|---|---|
| A1 Human reviews every order | Draft only, staff confirm | If Maria wants auto-confirm, invariant 1 is reversed and the accuracy bar must be far higher |
| A2 Odoo is writable by API | Yes | Need file import or screen automation; larger and more brittle |
| A3 "Fast and easy" means review time, not machine speed | 2 min per typical order | Wrong target measured |
| A4 Orders are in English | English only | Multilingual extraction and test data |
| A5 Orders are small-to-medium; 200-line ones are the stress case | Per notes | If many are large, review UI needs line-level filtering |
| A6 Customers and products already exist in Odoo | Yes; no creation of either | Unknown customers/products are flagged, not created |
| A7 Dec 2026 is the target | Yes, soft | A hard date forces a reduced v1 |

## 8. Decisions

- 2026-10-09 · Target is running before the December busy season: stated by Maria on the call.
- 2026-10-09 · The ERP is Odoo and stays the system of record: stated by Maria on the call.

No other decisions have been made by the owner. Everything above marked *assumed* needs her confirmation.

## Next step

Send Maria questions 1–2 (they block the build; she travels next week, so send them in writing). Then use
`verify-loop` to turn the invariant checks above into the exit check, and `plan-work` for slices. Don't design
before Odoo access (Q1) and samples (Q2) are in hand.
