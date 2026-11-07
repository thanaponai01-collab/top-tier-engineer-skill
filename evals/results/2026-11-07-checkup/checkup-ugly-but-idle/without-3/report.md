The layout is reasonable, but the business logic has been copied into two places and has already drifted apart more than once. The worst current bug isn't drift: **the receipt doesn't match what the customer is charged.** I ran the tests (2 pass) and one sample checkout. I didn't change anything.

## How it's structured

The good parts: it's small (about 210 lines) and split by job: `catalog`, `cart`, `receipt`, `payments`, `notify`, with `checkout` tying them together and `app.py` as a thin entry point. Old code is kept separate in `legacy/`.

The weak parts:
- **Pricing rules exist twice.** `shop/cart.py:3-15` and `shop/receipt.py:3-24` each define their own discount constants and their own discount math. The git history shows the cost: of 12 commits after the first, 5 changed both files in step, and 2 were fixes for the two drifting apart ("receipt total differs from cart for members", "round the discount differently"). Commit `82b04a5` changed only `cart.py`, which is how they first diverged. The test added in `1a0f135` only shows that the two copies still agree. It doesn't fix the cause.
- **Checkout works out the total twice by different routes.** `checkout.py` charges `cart_total + sales_tax`, then calls `render()`, which recalculates the total from scratch through `receipt_total` and leaves tax out.
- **Payments and email are hard-wired to real network calls** (fixed hosts, `time.sleep`), so neither can be tested. That's why the only tests cover the arithmetic.
- **Tax is a 64-line chain of nested `if`s** in `legacy/tax_tables.py` with no tests. Checkout always passes the category `"general"`, so most of it never runs.

## Fix first, in order

**1. The receipt total leaves out tax, so customers see a different amount from what they paid.**
With 3 tees + 2 caps, as a member, in the north region: the card is charged **100.95**, but the receipt says **TOTAL 94.35**. Every taxed order has this problem. To fix it, work out the total once in `checkout`, including tax, then charge that amount and print that amount on the receipt (with a tax line). `render` should take the totals as input instead of recalculating them. Then add a checkout test that checks the charged amount equals the receipt total.

**2. Keep one copy of the pricing rules.**
Delete `receipt_total` and its duplicate constants, and have the receipt use the totals from the cart/pricing code. This ends the kind of drift that has caused bugs twice already, and it's what makes fix #1 stay fixed. The current "receipt matches cart" test can then go, replaced by real tests of the discount thresholds and rounding.

**3. Payment retries can charge a customer twice.**
`shop/payments.py:10-22` sends the same `POST /charge` up to 4 times. It retries on 502/503 and on any `OSError`, and a timeout counts as one, even when the server may already have handled the charge. Nothing tells the server that the retries are the same charge. Send an idempotency key (for example, based on `order_id`) if the provider supports one. If it doesn't, only retry when the request clearly never got there. While doing this, make the HTTP client replaceable in tests so payments finally get covered.

## Later
- **Email:** `send_order_email` runs after the charge, inside the same request. It can block for up to about 37 seconds (3 × 10-second timeouts plus the waits between tries), and its failure is ignored silently. It should go on a queue or background job and at least be logged.
- **Tax tables:** add tests that pin down the current results before anyone touches this code. In the `east`/`clothing` branch, the rate depends on whether the amount in cents is odd or even (`cents % 2`). That looks like a porting bug, but someone who knows the old till rules should confirm it before it's changed. It doesn't run today, because checkout always passes `"general"`.
- **Small things:** an unknown SKU raises a bare `KeyError`, and `app.py` doesn't check its arguments.