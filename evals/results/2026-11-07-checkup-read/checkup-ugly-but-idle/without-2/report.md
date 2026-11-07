The codebase is small (about 200 lines) and the module layout is reasonable: cart, catalog, checkout, payments, notify and receipt each have one job, and `checkout.py` ties them together. The real problems are a few specific spots, and the git history shows where they are. I didn't change anything. I ran the two tests (both pass) and one checkout calculation.

## The three fixes, in order

**1. The discount rules are written twice, and the copies keep drifting apart.**
`shop/cart.py:3-15` and `shop/receipt.py:3-24` each have their own discount constants and their own discount calculation. Of the 12 commits after the initial one, 6 are about discounts. Every rule change had to be made in both files, and three were follow-up fixes after the copies disagreed:
- `82b04a5` changed only the cart, and `716a01b` fixed the receipt afterwards.
- `fa4e4f0` fixed the two files rounding differently.
- `6c240fd` fixed the bulk percentage in both.

The test added in `1a0f135` catches the drift but doesn't remove the cause. **Fix:** have the receipt call `cart_total` (or one shared pricing function) and delete the second copy. This is the cheapest of the three and stops the most frequent kind of bug.

**2. The receipt total doesn't match what the customer is charged.**
`checkout.py:9-11` charges the cart total plus sales tax, but `render()` prints the total before tax. I checked it with 3 tees and 2 caps for a member in the north region: the customer is charged **100.95** and the receipt says **TOTAL 94.35**. Two related problems:
- Tax is always calculated with category `"general"` (`checkout.py:10`). The catalog has no product categories, so T-shirts never get the clothing rates.
- The current test only checks receipt against cart, so it passes while the receipt is wrong.

**Fix:** work out one order total (discounts plus tax) in a single place, pass it to both `charge()` and `render()`, and test that the receipt matches the amount charged. Add product categories to the catalog at the same time. This could be ranked first because customers see it, but doing fix 1 first makes it a much simpler change.

**3. Payment retries can charge a customer twice.**
`payments.py:10-20` retries on any `OSError`, and a read timeout counts as one. If the payment provider processes the charge but the response takes longer than 15 seconds, the code sends the charge again, and there's no idempotency key to stop the provider applying it twice. The retry code has also needed constant fixing: 4 commits across `payments.py` and `notify.py`, each with its own hand-written retry loop. **Fix:** send an idempotency key (the order ID would work), only retry when it's safe to, and move both loops into one shared retry helper. That helper would also fix two smaller issues in `notify.py`: it sleeps uselessly after the last failed attempt, and it retries 4xx errors.

## Leave for later

`legacy/tax_tables.py` is the ugliest code in the repo: deeply nested `if` statements, and an odd rule in the east region that depends on whether the amount is even (`:42`). But it hasn't changed since it was added in the first commit, so it isn't causing problems now. Turn it into a data table only once you have tests that lock in its current outputs. Doing that tidy-up first would mean spending the quarter on the code that has caused the least trouble.

Other gaps worth noting: there are no tests for checkout, payments or tax. The payment and email URLs are hard-coded, so there's no way to swap in test or staging versions. `app.py` crashes on an unknown product code.