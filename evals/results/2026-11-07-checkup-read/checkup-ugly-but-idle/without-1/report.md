The code is small and mostly easy to follow. It has one real structural flaw, and that flaw causes most of the bugs in the git history. I read all 13 tracked files and the 13 commits, ran the tests (2 pass), and ran one checkout total by hand. I changed nothing.

## How it's structured

**What's good:**
- The modules are split sensibly: `catalog`, `cart`, `receipt`, `payments`, `notify`, and `checkout`, which ties them together.
- Money is kept in whole cents, so there are no floating-point rounding errors.
- `app.py` is a thin entry point.
- The code that calls outside services is kept in its own files.

**What's wrong:**
- **The discount rules are written twice.** `shop/cart.py:3-15` and `shop/receipt.py:3-24` each define the same constants and work out the discount separately. The history shows what this costs: 4 of the 12 changes since the first commit fixed the two copies disagreeing. They are `716a01b`, `fa4e4f0` and `6c240fd`, plus `82b04a5`, which updated only `cart.py` and caused the next fix. The test in `1a0f135` papers over this rather than fixing it.
- **No single function owns "what the order costs".** `checkout.py` adds tax. The receipt works out its own total separately, without tax.
- **Tests only cover the discount.** Nothing tests checkout, tax, payments or notifications.
- **`legacy/tax_tables.py` is ugly but stable.** It's deeply nested and has an odd/even-cents rule for east-region clothing. But it hasn't changed since it was imported, and checkout only ever passes `"general"`, so most of its branches never run. It isn't a priority.

## The three fixes, in order

**1. The receipt total doesn't match what the customer is charged.**
`checkout()` charges the cart total plus tax, but `render()` prints `receipt_total()`, which leaves tax out. I ran 3 tees and 2 caps for a member in the west region: the charge is **$100.95**, but the receipt says **TOTAL 94.35**. Every customer in a taxed region gets a receipt that disagrees with their card statement. This is the only problem I confirmed is already affecting customers, so it goes first.

**2. Calculate the price in one place.**
Write one function that returns subtotal, discount, tax and total. Then have `cart`, `receipt` and `checkout` all read from it, and delete the duplicate constants and logic in `receipt.py`. This fixes the root cause of #1 and of the four drift fixes. Do it together with #1, or straight after, so the receipt fix doesn't become a third copy. Add a test that checks the charged amount equals the printed total.

**3. Payment retries can charge a customer twice.**
`shop/payments.py:10-20` retries on a 502, a 503 or any `OSError`, and sends no idempotency key. A 502 or a read timeout can arrive after the payment provider has already taken the money. When that happens, the retry takes it again. Send the order ID as an idempotency key, if the provider supports one. If it doesn't, stop retrying once the request has been sent. Also add tests that use a fake payment server.

**Next in line, but not top three:**
- `checkout` ignores whether the order email was sent, and can wait up to about 7 seconds for it inside the request.
- The legacy tax module should get tests that pin its current behaviour before anyone tidies it up.