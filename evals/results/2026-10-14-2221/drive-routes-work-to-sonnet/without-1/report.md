The pricing changes are in. `python acceptance/check.py` passes 6/6 and the 3 existing tests still pass.

**What changed**
- **`shop/cart.py`**:
  - `Cart` now takes an optional `region` and has `apply_coupon(code)`.
  - Lines of 10 or more units get 10% off.
  - `SAVE5` takes 500 cents off after the bulk discount, never going below zero.
  - Tax rates are CA 7.25%, NY 8.875% and OR 0%.
  - `total()` returns subtotal, discount, tax and total. All percentages round half up to the cent.
  - `subtotal()` and `line_total()` work as before, still without discounts.
- **`shop/invoice.py`**: the invoice now ends with `Subtotal`, `Discount`, `Tax` and `Total` lines. The discount is shown with a minus sign, e.g. `-17.50`.

**Decisions you may want to check**
1. **Invoices for carts without a region.** The spec says `total()` raises `ValueError` when there's no region, but the existing test `test_invoice_total_line` prints an invoice for `Cart()` and expects the last line to be the total. To keep that test passing, an invoice for a cart with no region keeps the old single `Total` line (the undiscounted subtotal, no tax). An unknown region still raises. The alternative is to show tax as 0 for these carts, but that would print a wrong amount without any warning.
2. **"One coupon per cart."** Applying a second coupon raises `ValueError`, even if it's the same code again. Replacing the first coupon would also fit the spec, so tell me if you'd prefer that.

As an extra check, a CA cart with 10 mugs and `SAVE5` comes out as subtotal 12500, discount 1750, tax 779 and total 11529.

The session cost about $0.14.