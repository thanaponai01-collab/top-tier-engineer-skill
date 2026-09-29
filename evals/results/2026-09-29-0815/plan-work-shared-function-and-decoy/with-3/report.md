**Two slices, not three — and they can run in parallel.** The discount and tax-exempt rules both rewrite the same lines of `invoice.total()`, so they're one slice with one owner, not two independent hand-offs. The CSV export is a separate slice (new `export.py` file, only calls `total()` as a black box) and can safely run at the same time as the pricing-rules slice.

| slice | files | depends on |
|---|---|---|
| 1. Customer pricing rules (discount % + tax-exempt) | `models.py`, `invoice.py`, `test_invoice.py` | none |
| 2. CSV export of invoices | new `export.py` (+ test) | none |

Key traced fact: `invoice.total()` (fixture/invoice.py:8) is the single place every amount comes from — README even states this as the app's invariant — so any change touching "amount" collides there. Discount and tax-exempt both need it, hence merged into one slice with a settled order-of-operations rule (discount first, then tax on the discounted amount, tax-exempt zeroes the tax term). Export only *reads* `total()`, never reimplements it, so it's safe in parallel.

Full detail, hand-computed expected values, and the compatibility contract between the two slices are written to `fixture/PLAN.md`. Not checked: whether `report.py`'s text output or existing sample customers should also get discount/exemption values — neither was requested.

<!-- file written by the agent: fixture/PLAN.md -->
# PLAN.md

## Exit check (whole goal)

    python -m unittest        # existing + new tests, all green
    python export.py          # prints/writes a CSV row per invoice with a correct amount

Existing sample data (fixture/data.py), by hand, with no discount and no exemption (today's
behavior, must stay true after every slice):

| invoice | customer     | subtotal | tax             | total |
|---------|--------------|----------|-----------------|-------|
| inv-1   | Somchai (TH) | 10000    | 7% → 700        | 10700 |
| inv-2   | Acme Inc (US)| 120000   | 0%              | 120000|
| inv-3   | Hans GmbH(DE)| 12000    | 19% → 2280      | 14280 |

## Order-of-operations decision (settled before either pricing slice starts)

Discount and tax-exempt both change `invoice.total()`'s one calculation, so the order is fixed
once, up front, not left to whichever slice lands first:

**Discount applies to the subtotal first; tax (if any) is computed on the discounted amount; a
tax-exempt customer pays no tax regardless of discount.**

`total = discounted_subtotal + (0 if customer.tax_exempt else round(discounted_subtotal * rate_for(region)))`
`discounted_subtotal = round(subtotal * (1 - discount_pct/100))`

## Slices

| slice | files it will touch | check (command → expected, worked out by hand) | depends on |
|---|---|---|---|
| 1. Customer pricing rules (discount % + tax-exempt) | `models.py` (add `Customer.discount_pct: float = 0`, `Customer.tax_exempt: bool = False`), `invoice.py` (`total()` per the order above), `test_invoice.py` (new cases) | `python -m unittest` → new cases pass: (a) TH customer, discount_pct=10, subtotal 10000 → total **9630** (10000×0.9=9000, +7%×9000=630); (b) DE customer, tax_exempt=True, subtotal 12000 → total **12000** (no tax); (c) DE customer, discount_pct=20, tax_exempt=True, subtotal 10000 → total **8000** (discount only). Existing 4 tests in `test_invoice.py` still pass unchanged (defaults preserve today's numbers). | none |
| 2. CSV export of every invoice | new file `export.py` (reads `data.INVOICES`, calls `invoice.total()`), optionally `test_export.py` | `python export.py` → one CSV row per sample invoice, amount = `total()`'s cents: `inv-1,Somchai,10700` / `inv-2,Acme Inc,120000` / `inv-3,Hans GmbH,14280` (today's numbers — export doesn't know about discount/exemption, it only calls `total()`) | none |

Only two slices: the discount rule and the tax-exempt rule are **one slice, not two**, because both
rewrite the same lines of `invoice.total()` and their interaction (does a discounted, tax-exempt
invoice look different from a discounted, taxed one?) has to be decided once, by one owner, not
merged from two independent edits to the same function.

## What can run at the same time

**Slice 1 and Slice 2 can run in parallel.** Checked against the three tests in the skill:
- Different files: Slice 1 touches `models.py` + `invoice.py` + `test_invoice.py`; Slice 2 touches
  only a new `export.py` (+ its own test file). No overlap.
- No shared function/schema whose meaning changes for both: `export.py` calls `invoice.total(inv)`
  as a black box — it never reads `Customer.discount_pct` / `tax_exempt` or reimplements the
  calculation. Slice 1 changes `total()`'s internals but not its signature (still `total(invoice)
  -> int cents`) or its output for today's sample data (defaults are 0 / False, so existing numbers
  are unchanged — that's the compatibility contract Slice 1 owes).
- Neither reads what the other writes: Slice 2 never touches `models.py`/`invoice.py`; Slice 1
  never touches `export.py`.

The one thing that must NOT be split further: do not hand "discount" and "tax-exempt" to two
different agents as if they were independent — they both edit `total()` and the order-of-operations
sentence above is the contract between them. One agent owns Slice 1 end to end.

## Integration check (run after every merge)

    python -m unittest
    python export.py

Both slices merged should still show the exit-check table above for the three sample invoices
(none of them has a discount or exemption set in `data.py`), plus Slice 1's three new hand-computed
cases passing.

## Not checked

- Whether `report.py`'s plain-text output should also reflect discount/exemption — not requested,
  left untouched.
- CSV column names/format (dollars vs cents, header row) — left to Slice 2's implementer; only the
  amount values are pinned here since that's what "with its amount" requires.
- Whether any *existing* customer in `data.py` should get a non-default discount or exemption set —
  not requested; the plan only adds the capability.
