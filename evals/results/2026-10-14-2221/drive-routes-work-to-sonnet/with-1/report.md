The pricing changes from SPEC.md are in, `python acceptance/check.py` passes 6/6, and the 3 existing tests still pass.

**What changed:**
- **`shop/cart.py`**:
  - `Cart` now takes an optional `region` and has `apply_coupon()`.
  - A line of 10 or more units gets 10% off. `SAVE5` then takes 500 cents off, never going below zero.
  - Tax for CA, NY and OR is charged on what's left after both discounts.
  - `total()` returns the four amounts the spec asks for. Percentages are rounded half up to the cent.
- **`shop/invoice.py`**: the invoice now ends with `Subtotal`, `Discount` (shown negative), `Tax` and `Total`.

**Decisions for you to confirm:**
1. **Invoices for carts with no region.** The spec says `total()` must raise for a cart with no region, but an existing test prints an invoice for a plain `Cart()` and expects its last line to show the old total. So carts with no region keep the old one-line, pre-tax invoice. Carts with an unknown region raise `ValueError`, as the spec says. If you'd rather a no-region invoice also raise, that existing test would need changing.
2. **A second coupon raises `ValueError`.** The spec only says "one coupon per cart", so I chose to reject a second coupon rather than silently replace the first.

**Evidence:**
- Before any changes, the acceptance check failed 0/6, so it does catch wrong code.
- The drive run record (`fixture/RUN.json`) is marked complete. Its final step reran both checks on the finished code.
- I also checked one case by hand: 10 mugs in CA with `SAVE5` gives 125.00 − 17.50 + 7.79 tax = 115.29, which matches the arithmetic.

There was no release. This was local only, which is all you asked for. The run contract is in `contract.json`, one level above `fixture/`. Total spend was about $0.23.