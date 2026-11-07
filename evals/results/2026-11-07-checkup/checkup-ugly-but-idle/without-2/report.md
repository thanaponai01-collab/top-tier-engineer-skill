Overall the structure is reasonable for a codebase this size (about 200 lines). Modules are split along sensible lines: catalog, cart, receipt, checkout, payments, notify, plus a quarantined `legacy/` tax module. The problems aren't in the layout. They're in where the business rules live, what the receipt shows, and how the I/O code handles retries. The git history shows this clearly: 10 of the 12 commits after the initial one are either a pricing-rule change or a fix for the previous change.

## What the history shows

- **The discount rules are written twice.** `shop/cart.py:3-15` and `shop/receipt.py:3-24` each define their own `MEMBER_DISCOUNT_PCT`, `BULK_THRESHOLD`, `BULK_EXTRA_PCT` and discount calculation. Of the 10 commits, 5 touched pricing, and 3 of those were fixes for cases where the two copies disagreed. One example: `82b04a5` changed the cart, then `716a01b` had to fix the receipt. The test added in `1a0f135` only checks that the two copies match; it doesn't remove the duplication.
- **Payment and email retries were built up one fix at a time.** `payments.py` and `notify.py` got 3 commits each: retry, then a fix to the retry, then another fix. Each file has its own hand-written retry loop.
- **`legacy/tax_tables.py` looks the worst but hasn't changed** since the first commit. It's messy and stable, so it's not where the cost is.

## The three fixes, in order

**1. The receipt total doesn't match the amount charged.**
`checkout.py:9-11` charges the discounted total plus sales tax. `render()` (`receipt.py:27-30`) prints a total it calculates separately, without tax. I ran an example: a member buying 3 tees and 2 caps in the north region is charged **100.95**, but the receipt says **TOTAL 94.35**. The receipt lines also show undiscounted prices and no discount or tax lines. This happens on every order where tax is above zero, and almost every region applies 6–8% tax to the "general" category, which is what checkout always uses. The fix: compute the total in one place (cart plus tax) and pass that result to the receipt. That also removes the duplicated discount rules, which ends the change-then-fix pattern for future pricing changes.

**2. Payment retries could charge a customer twice.**
`payments.py:10-20` retries after an `OSError` (including a read timeout once the request has already gone out) and after a 502/503. In both cases the payment provider may already have processed the charge. The request carries no idempotency key, so unless the provider de-duplicates on `order` (I can't tell from the code), a slow response can lead to a second charge. Fix: send an idempotency key, and only retry when the request definitely didn't reach the provider. This could reasonably come first. I put it second because #1 definitely happens on every taxed order, while this one depends on the provider's behaviour.

**3. Checkout makes slow network calls with no overall time limit.**
Checkout runs the payment and email calls in sequence, in the same request. In the worst case the payment step can take about 70 seconds (4 attempts × 15s timeout plus backoff) and the email about 37 seconds. The two retry loops have drifted apart as they were fixed. The email doesn't need to block checkout at all: queue it or send it in the background. Move retry and backoff into one shared helper with an overall deadline.

## What I'd leave alone for now

- **`legacy/tax_tables.py`:** checkout only ever passes `"general"`, so most of its branches (including the odd even/odd-cents rule for east-region clothing) never run. Don't refactor it. Add tests that record its current outputs first, in case anyone needs to change it later.
- **Tests:** there are only 2 (both pass). Nothing covers checkout, tax, payments, or the gap between receipt and charge described in #1. Add tests alongside each fix above rather than as a separate project.

I haven't changed anything.