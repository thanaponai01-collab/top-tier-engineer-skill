# Tax audit: moves

Applies to everything below: all changes ship behind the `TAX_V2` flag (off by default), and the
auth model stays as it is. Source: the 2026-10-06 tax review with finance.

## M1: one rounding rule
- What: compute line tax with `round_half_up` everywhere, replacing the two local helpers.
- Why: `cart.py` and `invoice.py` round differently, so a cart and its invoice differ by a cent on ~2% of orders.
- Where: `cart.py:41`, `invoice.py:88`, new `money.py`
- Proof: `python -m pytest tests/test_tax.py -k rounding` passes, including the new case 10.125 -> 10.13
- Order: first

## M2: tax per line, not per order
- What: apply the rate to each line before summing.
- Why: mixed-rate carts (food + non-food) are taxed at the first item's rate today.
- Where: `cart.py:52-70`
- Proof: `python -m pytest tests/test_tax.py -k mixed_rates` passes; cart [food 10.00, book 20.00] -> tax 2.70
- Order: after M1

## M3: clean up the rounding helpers
- What: tidy up the old helpers once M1 lands.
- Why: dead weight.
- Where: `utils/num.py`
- Order: after M1

## M4: show tax breakdown on the invoice PDF
- What: one row per rate on the invoice PDF.
- Why: finance needs it for the quarterly filing.
- Where: `invoice_pdf.py:120`
- Proof: `python scripts/render_invoice.py --order 1001` shows a "VAT 7%" and a "VAT 19%" row
- Order: after M2
