# Plan: discount, tax-exempt flag, CSV export

**Two of the three can run together; the discount and the exemption cannot.** Read: `README.md`,
`models.py`, `invoice.py`, `tax.py`, `report.py`, `data.py`, `test_invoice.py`.

## The catch

Both the discount and the tax-exempt flag have to change the same function, `total()` in
`invoice.py`, and the answer depends on the order they are applied in: a discount taken off the
subtotal before tax gives a different number from one taken off after it, and an exempt customer
changes what "before tax" means. Two agents editing that function at the same time will conflict,
and even a clean merge can produce the wrong number. So one agent owns `total()` and does the
discount first, then the exemption; or a first slice settles the order of operations in a sentence
and a test, and the other slices build on it.

## Slices

| # | slice | files | can run alongside | check (command, and what counts as success) |
|---|---|---|---|---|
| 1 | discount: `Customer.discount_pct`, applied to the subtotal before tax in `total()` | `models.py`, `invoice.py` | the CSV export | `python -m unittest` plus a new test: subtotal 10000, 10% off, TH; expected result 9630 |
| 2 | tax-exempt flag: `Customer.tax_exempt`, `total()` skips tax when set; goes after slice 1 | `models.py`, `invoice.py` | the CSV export | `python -m unittest` plus a new test: exempt TH customer, subtotal 10000; must equal 10000 |
| 3 | CSV export: a new `export.py` that calls `total()`, one row per invoice | `export.py` only | slices 1 and 2: it is a separate new file that only calls `total()` and touches nothing they change | `python -c "import data, export; print(export.to_csv(data.INVOICES))"`; expected output is a header and 3 rows whose amounts equal `total()` for each invoice |

Slice 3 is safe to hand to another agent now: it is independent of the other two. Slices 1 and 2 go
to one agent, in that order.

## After they land

Merge in order, and after each merge run the whole suite, not just the slice's own test: work that is
green on its own branch is not proven green together. `report.py` prints through `total()`, so
`python report.py` after slice 2 is the last check.

Not checked: I ran nothing; this is a plan, and the numbers in the checks are worked by hand.
