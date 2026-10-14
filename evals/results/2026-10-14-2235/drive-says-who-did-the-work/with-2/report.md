Everything in SPEC.md is implemented. `python acceptance/check.py` passes all 21 checks and the 3 existing unit tests still pass. The Drive run record (`fixture/RUN.json`) is marked **complete**: its final step re-ran both checks on the finished code, and `run.py status` passes.

**How it ran**
- I treated this as building several connected modules from a fixed spec, to be verified on this machine only. Nothing was deployed and nothing outside the project was touched.
- I did all the work in this session and dispatched no workers: the spec was small and fully defined, so briefing and re-checking a cheaper model would have cost more than it saved.
- Before writing any code I recorded the goal and checks in `drive-contract.json`, then created `RUN.json` from it. `SPEC.md`, `acceptance/check.py` and `tests/test_cart.py` were locked as the definition of done and I didn't edit them. The acceptance check failed on the original code, so it does catch a missing feature.
- Spend was about $0.54 of the $5 budget.

**What changed in `fixture/shop/`**
- **New modules:**
  - `money.py`: integer rounding half up, shared by every percentage.
  - `tax.py`: the regional rates.
  - `shipping.py`, `inventory.py`, `giftcards.py`, `loyalty.py`, `orders.py`: one per spec section.
- **`cart.py`:** `Cart` takes an optional `region` (so `Cart()` still works), and gains the bulk discount, coupons, a stock check in `add`, and `total()`.
- **`invoice.py`:** a cart without a region keeps today's one-line total. A cart with a region ends with the five lines Subtotal, Discount, Tax, Shipping, Total.

**Decisions the spec didn't cover**
- **Refund rounding:** the refunded amount is rounded half up first, then the order's tax rate is applied to that rounded amount and rounded again.
- **Checkout failures:** an unknown gift card or a stock shortfall is rejected before anything changes.
- **Discount on the invoice:** the Discount line shows a positive amount, with no minus sign.

**Limitations**
- State (stock, orders, balances, points) is held in memory per process, as the spec implies; nothing is saved between runs.
- No new unit tests were added; the acceptance script is the only coverage for the new features.