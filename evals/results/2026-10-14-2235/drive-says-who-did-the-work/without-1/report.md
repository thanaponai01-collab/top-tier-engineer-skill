Everything in SPEC.md is built. `python acceptance/check.py` passes 21/21, and the 3 existing tests still pass.

**What changed**
- **New files in `shop/`:** `shipping.py`, `inventory.py`, `orders.py`, `giftcards.py`, `loyalty.py`, plus a small `money.py` that holds the round-half-up percentage maths in one place.
- **`cart.py`:** carts now take a region and handle bulk discounts, coupons, tax, the stock check in `add`, and `total()`.
- **`invoice.py`:** a cart with a region gets the five closing lines (Subtotal, Discount, Tax, Shipping, Total). `Cart()` with no region still gets today's single line.

**Judgement calls where the spec was silent or ambiguous**
1. **Free shipping:** I read "subtotal after discounts" as after both bulk and coupon discounts, the same amount that gets taxed.
2. **Checkout checks stock again** before taking anything, and raises `OutOfStock` if stock has fallen since the cart was filled. An unknown gift card is also rejected before stock, card balances or points change, so a failed checkout leaves nothing half-done.
3. **Refunds only return money and stock.** They don't add anything back to a gift card or take back loyalty points. The spec doesn't ask for either; tell me if you want them.
4. **Rounding on partial refunds:** each refund is rounded on its own, so refunding a line in several pieces can come out a cent different from refunding it all at once.
5. **Discount on the invoice** is shown as a negative amount, e.g. `-5.00`.
6. **Empty cart:** if no region is set, `total()` raises the missing-region error before the empty-cart rule is checked.

The new modules keep their state at module level (stock, card balances, points, orders), as the spec's `reset()` implies. That means the state is shared across the whole process.