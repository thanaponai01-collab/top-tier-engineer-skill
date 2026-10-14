Everything in SPEC.md is built. `python acceptance/check.py` passes 21/21, the 3 existing tests still pass, and the Drive run record (`fixture/RUN.json`) is marked complete after a final rerun of both checks.

**How it ran:** I treated this as building new features from a spec, run locally with nothing to deploy. Before any code, `acceptance/check.py` failed on an import error because the new modules didn't exist, so the check does catch an incomplete build. The job was small enough that I did it myself without handing it to helper agents, which kept the cost to about $0.53.

**What changed in `fixture/shop/`:**
- **New files:**
  - `money.py`: rounds percentages and partial-line amounts half up, working in exact decimals rather than floats.
  - `inventory.py`, `shipping.py`, `giftcards.py`, `loyalty.py`, `orders.py`: one per SPEC section.
- **`cart.py`:**
  - `Cart` takes an optional `region` and has `apply_coupon`.
  - Adding to the cart checks stock.
  - `total()` applies the bulk discount, then the coupon (it can't take the cart below zero), then tax, then shipping. The free-shipping check uses the subtotal after both discounts.
- **`invoice.py`:** a cart with a region ends with the five lines. A `Cart()` with no region still gets today's one-line invoice.

**Choices the spec didn't settle:**
- Checkout validates everything first (cart not empty, region, gift card code, stock) and only then changes stock, gift card balances or points, so a failed checkout leaves nothing half done.
- An order keeps each line's price after the bulk discount and its tax rate, and refunds are worked out from those. Refunding a sku that wasn't on the order, or a quantity below 1, raises `ValueError`.
- On a regional invoice, the Discount line shows a positive amount, with no minus sign.

**Limits:** Stock, orders, gift card balances and points live in memory only, as the spec implies. My contract file is `contract.json`, one level up next to `fixture/`. The only test suites are the acceptance script and the 3 existing tests; I didn't add separate unit tests for the new modules.