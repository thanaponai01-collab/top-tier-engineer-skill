Everything in SPEC.md is implemented. `python acceptance/check.py` passes 21/21, and the 3 existing unit tests still pass. Spend was about $0.40 of the $5 budget.

**What changed in `fixture/shop/`**
- **`cart.py`:** `Cart` now takes an optional `region`, applies the bulk discount, takes one coupon, checks stock in `add`, and has `total()`. `line_total` and `subtotal` behave as before.
- **`invoice.py`:** carts with a region end with the five lines; a cart with no region keeps the old one-line total.
- **New files:**
  - `shipping.py`, `inventory.py`, `giftcards.py`, `loyalty.py` and `orders.py`, each covering its section of the spec.
  - `money.py`, a small shared helper that applies percentages and rounds half up to the cent, so rounding is the same everywhere.

**Decisions the spec left open**
- **Bulk discount:** it is rounded per line, so a 15-tee line gets 29.99 off, not 29.985. The acceptance numbers depend on this.
- **Coupon floor:** a coupon is limited to what is left after bulk discounts, so the discount never goes over the subtotal.
- **Checkout is all-or-nothing:** a bad gift card or short stock raises an error before anything changes. Stock is checked again at checkout, because two carts can each hold the same last units.
- **Refunds:** each order stores its lines (price after bulk discount) and its region, so a refund uses the tax rate from when it was bought. Refunding a sku the order doesn't contain, or a quantity under 1, raises `ValueError`.
- **Loyalty:** a checkout with no customer earns no points.
- **CSV export:** it uses Python's `csv` module, so a customer name containing a comma comes out correctly quoted.

I added no new unit tests beyond the acceptance script.