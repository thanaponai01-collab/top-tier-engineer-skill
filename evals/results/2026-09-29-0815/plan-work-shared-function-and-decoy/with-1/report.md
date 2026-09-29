Read the whole fixture: `models.py` (Customer dataclass), `invoice.py` (single `total()` calc point — subtotal + tax), `tax.py` (region rate table), `report.py`/`data.py` (sample data, plain-text report), and the existing test suite. The README confirms `invoice.total()` is the single chokepoint for all amount math.

**Answer first:** 2 slices, not 3 — discount and tax-exempt must be built as one slice (same file, same calculation, order-dependent), while CSV export is fully independent and can run in parallel with it.

**Why discount + tax-exempt aren't separable:** both add a field to `Customer` in `models.py` and both change `invoice.total()`. They also interact: does the discount apply to the pre-tax or post-tax amount, and does a tax-exempt customer still get the discount? That's one calculation, not two — splitting it across two agents means whoever merges second silently picks the order. I fixed the order now so the slice can be built by a single owner without more back-and-forth: **discount applies to the subtotal first, tax is computed on the discounted subtotal, and skipped entirely if `tax_exempt`.**

**Why CSV export is safe to parallelize:** it's a new file that only calls `invoice.total(invoice)` as a black box — same signature, before and after slice 1 lands. It doesn't touch `models.py` or `invoice.py`, and slice 1's new fields default to no-op (`discount_percent=0`, `tax_exempt=False`), so the CSV numbers for the existing sample data are unaffected by slice 1 landing before or after it.

| slice | files it will touch | check (command → expected) | depends on |
|---|---|---|---|
| **1. Discount + tax-exempt** | `models.py` (add `discount_percent: float = 0`, `tax_exempt: bool = False` to `Customer`), `invoice.py` (`total()`: discount subtotal, then tax unless exempt), `test_invoice.py` | `python -m unittest` → new cases: HANS w/ 10% discount, subtotal 10000 → discounted 9000, DE tax 19% → **10710**; HANS `tax_exempt=True`, no discount, subtotal 10000 → **10000**; HANS `tax_exempt=True` + 10% discount → **9000** | — |
| **2. CSV export of invoices** | new file `csv_export.py` (reads `data.INVOICES`, calls `invoice.total()`) | `python csv_export.py` → exact rows (by hand, current rates, unaffected by slice 1's no-op defaults):`inv-1,Somchai,107.00`  `inv-2,Acme Inc,1200.00`  `inv-3,Hans GmbH,142.80` | — |

**Run together:** slices 1 and 2 — different files, no shared function whose signature changes, no read/write overlap (verified by opening `invoice.py` and confirming `total(invoice)` keeps its signature).

**Integration check** (run after each merge): `python -m unittest` all green, and `python csv_export.py` still matches the three rows above.

**What I did not check:** whether the CSV should include discount/tax-exempt as its own columns (the ask only said "amount," so I scoped it to amount only) — if that's wanted, CSV export would need to read the new `Customer` fields and would then depend on slice 1 landing first.