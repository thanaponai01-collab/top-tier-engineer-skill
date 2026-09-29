**2 slices, only one pair to hand out — and discount + tax-exempt are not one of them.**

- **Slice 1 — discount + tax-exempt (one owner, not splittable):** both add a field to `models.py::Customer` and both change the arithmetic in `invoice.py::total()`, and the order they apply in changes the answer. I opened both files — there's no clean split, so this is a single slice, done by one agent. Settled order: discount reduces the subtotal, tax is computed on the discounted subtotal, tax-exempt zeroes the tax term.
- **Slice 2 — CSV export:** new file, calls `invoice.total()` through its existing signature, never touches `models.py` or `invoice.py`. **Safe to run in parallel with Slice 1** — verified by reading every file either slice touches; no shared file, function, or field.

Full table, checks (with hand-computed expected values), and the three open questions I didn't resolve are in `fixture/PLAN.md`. Integration check after each merge: `python -m unittest` + `python export.py`.

<!-- file written by the agent: fixture/PLAN.md -->
# PLAN.md — billing app: discount, tax-exempt, CSV export

## Exit check (whole goal)

    python -m unittest        # all existing + new tests green
    python export.py          # or equivalent entry point; prints/writes CSV without error

Behavior that must hold, worked out by hand (not read off the code):

- `subtotal 10000, 10% discount, Thai tax(7%) → 9630` (discount applied to subtotal, then tax on
  the discounted amount — this is the order both money slices must use)
- Existing `test_invoice.py` cases unchanged: Somchai(TH) 10000→10700, Acme(US) 10000→10000,
  Hans(DE) 10000→11900 (new fields must default to no-op: 0% discount, not exempt)

## Why discount and tax-exempt cannot run in parallel

Both features change the same calculation and the same data shape:

- `models.py::Customer` — both need a new field on the same dataclass.
- `invoice.py::total()` (models.py:19, invoice.py:8-11) — both change the arithmetic inside the
  same function, and the order they apply in changes the result (discount-then-tax vs
  tax-then-discount give different totals). I opened both files; there is no way to split this
  so each agent only touches lines the other doesn't.

This is exactly the "shared piece" case: settled here as one sentence — **discount reduces the
subtotal first, tax is computed on the discounted subtotal, tax-exempt zeroes the tax term
regardless of region** — and built as a single slice by one owner, not two.

CSV export only ever calls `invoice.total()` (per README.md:6, "everything that shows an amount
asks `invoice.total()` for it"); it never reads or duplicates the tax/discount arithmetic, and it
adds a new file rather than editing `models.py` or `invoice.py`. So it is safe to build at the same
time as the money slice.

## Slices

| slice | files it will touch | check | depends on |
|---|---|---|---|
| 1. Discount + tax-exempt (one slice, one owner) | `models.py` (add `discount_pct: float = 0.0`, `tax_exempt: bool = False` to `Customer`), `invoice.py::total()` | `test_invoice.py` new cases, computed by hand: (a) TH customer, discount 10%, subtotal 10000 → 9630; (b) DE customer, tax_exempt=True, subtotal 10000 → 10000; (c) TH customer, discount 20% + tax_exempt=True, subtotal 10000 → 8000; (d) all four pre-existing cases in `test_invoice.py` still pass unchanged | none |
| 2. CSV export | new file (e.g. `export.py`), reads `data.INVOICES`, calls `invoice.total()` | `python export.py` (or `to_csv(INVOICES)`) produces, byte for byte:<br>`invoice_id,customer,amount`<br>`inv-1,Somchai,107.00`<br>`inv-2,Acme Inc,1200.00`<br>`inv-3,Hans GmbH,142.80`<br>(computed by hand from `data.py`'s sample invoices under current, pre-slice-1 tax rules — sample customers carry 0% discount / not exempt, so this check holds whether it lands before or after slice 1) | none |

## What runs together

**Slice 2 (CSV export) can run at the same time as Slice 1 (discount + tax-exempt).** Checked by
opening `models.py`, `invoice.py`, `data.py` and `report.py`: slice 2 touches no file slice 1
touches, calls `total()` only through its existing signature (`total(invoice) -> int`, unchanged by
slice 1), and reads no field slice 1 adds. Neither slice's file list overlaps the other's.

**Discount and tax-exempt themselves are not two parallel slices** — see "why" above. If handed to
two agents anyway, expect a merge conflict on `Customer` and a wrong total from whichever order the
merge happens to apply the two changes in.

## Integration check

After each merge, run the full exit check, not just the merging slice's own check:

    python -m unittest
    python export.py

## What I did not check

- Whether the CSV should include discount/exempt status as columns, or just id + amount as asked —
  planned for id + customer + amount only, per the literal request. Confirm before slice 2 starts
  if more columns are wanted.
- Whether discount is meant to be exclusive of or combined with tax-exempt for a given customer —
  slice 1's check (c) assumes both can be set on the same customer and compose (discount first,
  then zero tax); flag if that's not the intended interaction.
- Rounding behavior when discount_pct produces a fractional cent (used `round()`, matching the
  existing pattern in `invoice.py:11`) — not verified against a real Decimal/rounding spec since
  none exists in the current code.
