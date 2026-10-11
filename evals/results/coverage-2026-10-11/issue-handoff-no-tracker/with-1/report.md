I filed nothing, so the team won't find any issues tomorrow. Two things stopped it:

- **No remote:** the `fixture` repo has no git remote.
- **No login:** `gh` isn't authenticated. It needs `gh auth login` or a `GH_TOKEN`, and I can't do that in a non-interactive session.

I didn't touch `AUDIT.md`, since nothing was filed to stamp back into it.

I wrote the issue bodies so filing is quick once there's a remote and a login. They're in `C:\Users\thana\AppData\Local\Temp\tte-eval-6_ajt522\issue-bodies.md`.

- **Content:** each body copies the audit's What, Why, Where, Proof and Order lines verbatim. Each also starts with the shared context: the `TAX_V2` flag stays off by default, and the auth model doesn't change.
- **Label and order:** the batch label is `tax-audit`. Create them in the order M1, M2, M4, then add `Blocked by #N` to M2 and M4 once the numbers exist.

| item | issue | status | why |
|---|---|---|---|
| M1: one rounding rule | none | ready, not filed | no remote, `gh` not logged in |
| M2: tax per line | none | ready, not filed | same |
| M3: clean up rounding helpers | none | held | The item has no Proof line, and "tidy up / dead weight" names no concrete change. I couldn't fill the gap because `utils/num.py` isn't in the checkout. It needs a real scope and a check, for example removing the helpers and grepping for zero callers, before it's worth an issue. |
| M4: invoice PDF tax breakdown | none | ready, not filed | same as M1 |

I haven't run the `gh issue list` check for existing duplicates either, because `gh` can't reach the repo. Run it before creating, so a re-run doesn't double up the backlog.

<!-- file written by the agent: issue-bodies.md -->
# Issue bodies for fixture/AUDIT.md (NOT FILED: no git remote, gh not authenticated)

Label for the batch: `tax-audit`

Shared Context block (prepend to every body):
> **Context:** All changes ship behind the `TAX_V2` flag (off by default), and the auth model stays as it is. Source: the 2026-10-06 tax review with finance (`AUDIT.md`).

---
## M1: one rounding rule   (file first)
**Context:** (above)

- What: compute line tax with `round_half_up` everywhere, replacing the two local helpers.
- Why: `cart.py` and `invoice.py` round differently, so a cart and its invoice differ by a cent on ~2% of orders.
- Where: `cart.py:41`, `invoice.py:88`, new `money.py`
- Proof: `python -m pytest tests/test_tax.py -k rounding` passes, including the new case 10.125 -> 10.13
- Order: first

---
## M2: tax per line, not per order
**Context:** (above)

- What: apply the rate to each line before summing.
- Why: mixed-rate carts (food + non-food) are taxed at the first item's rate today.
- Where: `cart.py:52-70`
- Proof: `python -m pytest tests/test_tax.py -k mixed_rates` passes; cart [food 10.00, book 20.00] -> tax 2.70
- Order: after M1. Blocked by #<M1>

---
## M4: show tax breakdown on the invoice PDF
**Context:** (above)

- What: one row per rate on the invoice PDF.
- Why: finance needs it for the quarterly filing.
- Where: `invoice_pdf.py:120`
- Proof: `python scripts/render_invoice.py --order 1001` shows a "VAT 7%" and a "VAT 19%" row
- Order: after M2. Blocked by #<M2>

---
## M3: HELD, not filed
Missing Proof, and "tidy up the old helpers / dead weight" names no concrete change. `utils/num.py` is not in the repo checkout, so line numbers and a dead-code check could not be filled in.
