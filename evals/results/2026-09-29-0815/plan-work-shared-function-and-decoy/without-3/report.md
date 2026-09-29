## What's here

Small lib: `models.py` (Customer/Line/Invoice dataclasses), `invoice.py` (`subtotal`/`total`), `tax.py` (region rate table), `report.py` (plain-text report), `data.py` (sample data), `test_invoice.py`. The README states the contract: *"Everything that shows an amount asks `invoice.total()` for it; nothing else does the arithmetic."*

## The three pieces, mapped to files

1. **Per-customer discount %** — add a field to `Customer` (`models.py`), apply it in `invoice.total()`/`subtotal()` (`invoice.py`), extend `test_invoice.py`.
2. **Per-customer tax-exempt flag** — add a field to `Customer` (`models.py`), make `invoice.total()` skip `tax.rate_for()` when set (`invoice.py`, maybe `tax.py`), extend `test_invoice.py`.
3. **CSV export of invoices+amounts** — new file (e.g. `csv_export.py`), modeled on `report.py`: iterate `data.INVOICES`, call `invoice.total()` per invoice, write CSV. Touches no existing file's logic.

## Why 1 and 2 collide

Both discount and tax-exempt touch the *same* dataclass (`Customer` in `models.py`) and the *same* function (`invoice.total()`/`subtotal()` in `invoice.py`), and both will want to add cases to `test_invoice.py`. Worse, they interact: does the discount apply to the pre-tax subtotal or the post-tax total? Is a tax-exempt customer's discount still computed off the full subtotal? Whoever writes `total()` second has to know what the first did, and the two changes will produce merge conflicts on the same lines even if they don't logically interact. This is a single design decision (the order of operations inside `total()`) — it shouldn't be split across two agents working blind to each other.

## Plan

- **Do first, alone, decide-once:** settle the order of operations in `total()` — I'd suggest `subtotal → apply discount → apply tax unless exempt`, but that's a call worth confirming with you before handing it out. Whoever does this also adds both new `Customer` fields at once (discount + exempt), even if only one behavior lands right away — avoids a second edit to the same dataclass.
- **Then, sequentially, not concurrently:** discount logic, then tax-exempt logic (or vice versa) — each small, each re-running `test_invoice.py`.
- **In parallel with all of the above, safely:** the CSV export. It only calls `invoice.total()` as a black box and never touches `models.py`/`invoice.py`/`tax.py`, so it can't conflict with either feature and doesn't care which one lands first.

**Bottom line:** only the CSV export is safe to hand to an independent agent right now. Discount and tax-exempt both mutate `Customer` and `invoice.total()`, so give those to one agent (or sequence two agents) rather than running them side by side — otherwise you'll get merge conflicts plus a real question about which order the math happens in.

One thing I'd confirm before you dispatch anyone: **does the discount apply before or after tax, and does it apply at all for tax-exempt customers?** That answer changes what "done" looks like for two of the three pieces.