**Answer first:** 3 work items, but only 2 of them can run in parallel — the CSV export is independent; the discount and tax-exempt changes both land in the same function and file, so they should not run concurrently.

**Why (traced from the code):**

- `models.py` — `Customer` dataclass — currently `id, name, region`.
- `invoice.py::total()` — the single place amounts are computed: `subtotal + tax` — per README, "everything that shows an amount asks `invoice.total()` for it."
- `tax.py::rate_for(region)` — used by `total()`.
- `test_invoice.py` — asserts exact totals per region.
- `report.py` / `data.py` — read-only consumers of `total()` and `Customer`.

**The three pieces:**

1. **Percentage discount per customer** — add a field to `Customer` (`models.py`), apply it inside `total()` (`invoice.py`), extend `test_invoice.py`.
2. **Tax-exempt flag per customer** — add a field to `Customer` (`models.py`), branch on it inside `total()` (`invoice.py`), extend `test_invoice.py`.
3. **CSV export of every invoice + amount** — a new file (e.g. `export.py`) that iterates `data.INVOICES` and calls `invoice.total()` per invoice. Doesn't touch `models.py`, `invoice.py`, or `tax.py`, and doesn't care about their internals — only that `total(invoice)` keeps its signature.

**Why 1 and 2 collide:** both add a field to the same dataclass and both change the same arithmetic in `total()`. Whoever writes `total()` second has to know the *order* the two adjustments combine in (discount off subtotal before tax, or after; does an exempt customer still get the discount) — that's a single formula decision, not two independent edits. Done in parallel, the agents will step on the same lines in `models.py` and `invoice.py`, and even if the merge is clean, one agent's assumption about ordering can silently override the other's, and both will add cases to `test_invoice.py` around the same total() behavior.

**Recommendation:**
- Run **CSV export** in parallel with either of the other two — no shared file, no shared logic.
- Do **discount** and **tax-exempt** sequentially: one agent (or you) fixes the combined formula first (state it up front — e.g. "tax applies to the discounted subtotal, and exempt customers skip the tax term entirely regardless of discount"), lands it as one change, or lands the first then hands the second an explicit note of what `total()` now looks like so it extends rather than re-derives it.