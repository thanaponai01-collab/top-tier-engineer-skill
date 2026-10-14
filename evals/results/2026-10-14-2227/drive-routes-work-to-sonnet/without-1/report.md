All of SPEC.md is implemented. `python acceptance/check.py` passes 21/21 and the 3 existing unit tests still pass. I ran both from `fixture/`. This cost about $0.36.

**What changed in `fixture/shop/`:**
- **`cart.py`:** carts now take an optional `region`. I added bulk discounts, `apply_coupon`, sales tax and `total()`. `add` now checks stock.
- **`invoice.py`:** a cart with a region gets the five closing lines (Subtotal, Discount, Tax, Shipping, Total). A `Cart()` with no region still gets the old one-line invoice.
- **New files:** `shipping.py`, `inventory.py`, `giftcards.py`, `loyalty.py` and `orders.py` (checkout, refunds, CSV export and `reset`).
- **`money.py`:** a small shared helper I added. It does all percentage maths with exact fractions and rounds half up, so a rate like 8.875% doesn't pick up floating-point error.

**Decisions the spec didn't settle:**
- **Checkout validates everything before changing anything.** It checks the region, the gift card code and stock first, so a failed checkout leaves stock, gift card balances and points untouched.
- **Checkout checks stock again.** Stock can change between adding to a cart and checking out, for example when another order goes through first. If there isn't enough left, checkout raises `OutOfStock`.
- **Refunds leave the order's figures as they were.** The order's totals and its CSV export still show the original amounts; only which units have been returned is tracked.
- **Bad refund quantities are rejected.** Returning zero or a negative number raises `ValueError`, as does returning a sku that wasn't on the order.
- **The Discount line on the invoice shows a minus sign** (e.g. `-12.50`), and the cents formatter now handles negative amounts.
- **No new state is persisted.** Stock, gift card balances, loyalty points and the order list are held in memory, which is what `orders.reset()` and the acceptance checks expect.

I didn't add unit tests for the new features; the acceptance script is the only coverage for them.