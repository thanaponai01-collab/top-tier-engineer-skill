Everything in SPEC.md is built. `python acceptance/check.py` passes 21/21, and the 3 existing tests in `tests/test_cart.py` still pass. The drive run record (`fixture/RUN.json`) reran both checks on the final code and shows the run as **complete**.

**What changed in `fixture/shop/`**
- **`cart.py`:** carts now take an optional region. They handle bulk discounts, coupons, tax and a stock check when you add items, and `total()` returns the five amounts. `Cart()` with no region works as before.
- **`invoice.py`:** carts with a region end with the five lines Subtotal, Discount, Tax, Shipping and Total. Carts without one keep the old single Total line.
- **New files:** `shipping.py`, `inventory.py`, `giftcards.py`, `loyalty.py` and `orders.py` (checkout, refund, CSV export, reset). I also added a small `money.py` that does all percentage maths in whole cents, rounding half up, so floating-point errors can't creep in.

**Before and after:** before the change the acceptance check failed straight away (ImportError), and the 3 tests passed. I didn't edit `acceptance/check.py`, `SPEC.md` or the tests; the run record locks them so it would notice if they changed.

**Judgement calls where SPEC.md was silent:**
- **Shipping:** "subtotal after discounts" for free shipping means after both the bulk discount and the coupon.
- **Stock:** adding to a cart is checked against current stock, but nothing is held back until checkout. Checkout checks stock again before taking it, so two carts can't both sell the last items.
- **Bad gift card:** an unknown gift card is rejected at checkout before any stock or balance changes.
- **Bad refund:** refunding a quantity below 1, or a sku that wasn't in the order, raises `ValueError`.
- **Repeated refunds:** each partial refund on the same line is rounded on its own, so several small refunds can differ by a cent from one refund of the same units.

**Limitations:** stock, orders, gift card balances and points are kept in memory only; there's no database, matching how the spec describes it. The folder isn't a git repository, so nothing was committed. Spend was about $0.51 of the $5 budget, and I did the work directly without helper agents.