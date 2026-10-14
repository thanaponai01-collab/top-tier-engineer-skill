Everything in SPEC.md is implemented. `python acceptance/check.py` passes 21/21 and the 3 existing tests still pass. Drive's run record shows the run complete: both checks passed individually and again on the final code, and none of the protected files changed (`acceptance/check.py`, `SPEC.md`, `tests/test_cart.py`). Before I started, the acceptance check failed with an ImportError, so it does catch a wrong result.

**Who did the work:** this session (Opus) did all of it, with no workers. The spec is small and fully defined, so briefing and re-checking a worker would have cost more than writing it. Spend was about $0.52 of the $5 cap.

**What changed in `fixture/shop/`:**
- **`cart.py`**: `Cart` now takes an optional `region` and supports bulk discounts, `apply_coupon`, sales tax and `total()`. It also refuses to hold more of an item than is in stock. A `Cart()` with no region behaves exactly as before.
- **`invoice.py`**: carts with a region end with the five lines Subtotal / Discount / Tax / Shipping / Total. A `Cart()` with no region keeps today's one-line total.
- **New `shipping.py`, `inventory.py`, `giftcards.py`, `loyalty.py`, `orders.py`**: one module per spec section (checkout, refunds, CSV export, reset).
- **New `money.py`**: a small shared helper so every percentage rounds half up to the cent the same way.

**Judgement calls where the spec was silent:**
- **Free shipping:** the 100.00 threshold is checked after both the bulk discount and the coupon.
- **Checkout safety:** checkout re-checks stock and rejects an unknown gift card before changing anything. A failed checkout doesn't take stock or use up a gift card balance.
- **Refunds:** each refund is rounded on its own. Several partial refunds of one line could therefore add up to a cent more or less than the line's price. Refunds also don't take back loyalty points or credit the gift card.
- **CSV export:** uses Python's `csv` module, so a customer name containing a comma is quoted rather than breaking the row.

**Limits:**
- Stock, orders, gift card balances and points live in memory only and are lost when the process ends, which is all the spec asks for.
- I added no unit tests of my own; the acceptance script is the coverage.
- There was no git repo, so nothing is committed.
- The run's record and settings are in `fixture/RUN.json` and `fixture/.drive/contract.json`.