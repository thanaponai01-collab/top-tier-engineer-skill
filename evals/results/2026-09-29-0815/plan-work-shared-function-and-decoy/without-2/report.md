**Read:** `fixture/` is a 6-file billing lib. `models.py` defines `Customer`/`Line`/`Invoice` (dataclasses, no logic). `invoice.py` has `subtotal()` and `total()` — the single place that computes the amount due (subtotal + tax via `tax.rate_for(customer.region)`). `report.py`/`data.py` are text-report plumbing. Per the README, everything that shows an amount goes through `invoice.total()`.

## The three pieces

**A. Per-customer % discount**
- Add a field to `Customer` (e.g. `discount_pct`, default 0).
- Apply it inside `invoice.total()`: reduce the subtotal by the discount before tax is calculated.
- Extend `test_invoice.py` with discount cases.

**B. Per-customer tax-exempt flag**
- Add a field to `Customer` (e.g. `tax_exempt`, default `False`).
- Apply it inside `invoice.total()` (or by short-circuiting the call to `tax.rate_for`): skip tax entirely when set.
- Extend `test_invoice.py` with exemption cases.

**C. CSV export of invoices + amounts**
- New module (e.g. `csv_export.py`) that iterates invoices and writes `id, customer, total()` per row, using `invoice.total()` as-is — it treats `total()` as a black box, doesn't touch its internals or signature.
- New test file for it, using `data.py`'s sample invoices.

## What can run in parallel

**A and B cannot run in parallel with each other.** Both add fields to the same `Customer` dataclass and both rewrite the same few lines inside `invoice.total()`. Worse, they interact: does the discount apply before or after checking exemption, does discount get computed off the pre-tax or post-tax subtotal — that's one design decision either way, not two independent ones. Two agents editing `total()`'s body at the same time will produce a merge conflict at best, and silently wrong combined math at worst (e.g. one agent's exemption check landing above the other's discount line without knowing it needs to). Give A and B to the same agent as one task, or run them strictly sequentially (A merges, then B rebases on it).

**C can run in parallel with A and/or B.** It only calls `invoice.total(invoice)`, whose signature isn't changing, and never touches `models.py` or `invoice.py`. It doesn't need to know whether discounts or exemptions exist yet — it'll pick up correct totals automatically once A/B land, and even if it lands first, nothing about it needs revisiting.

So: **one agent for A+B together** (sequential inside that task), **one agent for C**, both starting at the same time.