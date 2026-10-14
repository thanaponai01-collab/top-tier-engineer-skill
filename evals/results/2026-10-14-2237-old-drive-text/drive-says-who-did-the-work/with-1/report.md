Everything in SPEC.md is built. `python acceptance/check.py` passes 21/21 and the 3 existing tests still pass. The run record says `RUN: complete`; its final step reran both checks against the finished code. Spend was about $0.35 of the $5 budget. This was local work only: nothing was deployed and no external actions were taken.

**What changed in `fixture/shop/`**
- **Changed:** `cart.py` now handles region, coupons, bulk discount, tax and `total()`, and checks stock in `add`. `invoice.py` adds the five closing lines when a cart has a region; a `Cart()` with no region still gets today's one-line invoice, which I checked by hand.
- **New:** `shipping.py`, `inventory.py`, `giftcards.py`, `loyalty.py` and `orders.py` (checkout, refund, export, reset), plus a small `money.py` that does the percentage-and-round-half-up maths in whole cents.

**Choices I made where the spec was silent**
- **Shipping:** it's free when the subtotal after bulk discount *and* coupon reaches 10000.
- **Stock at checkout:** checkout checks stock again before taking anything, because stock may have changed since the items were added. It also rejects an unknown gift card before any stock, balance or points change.
- **Refunds:** a refund of 0 units, or of a sku that wasn't on the order, raises `ValueError`.
- **Invoice discount:** the Discount line shows the amount as a positive number.

**Limitations**
- Stock, orders, gift cards and points live in memory for the life of the process. Nothing is saved.
- I didn't add unit tests for the new modules; the acceptance check is what covers them.
- Running the same cart through checkout twice isn't blocked.

The run record is `fixture/RUN.json`; the frozen contract it was started from is in `drive-meta/contract.json`, outside the fixture.