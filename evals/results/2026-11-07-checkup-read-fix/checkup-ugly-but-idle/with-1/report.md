## Checkup: `fixture/` shop

**What was measured:** 13 tracked files (12 of them code) and all 13 commits of history. The structure, import-graph and dependency helpers ran. There is no FEATURES.md, so "easy to find things" couldn't be measured. "Tests that can fail" is never measured by this check.

### How well it's structured

| Property | Rating |
|---|---|
| Easy to find things | not checked |
| One change in one place | **poor** |
| Dependencies point one way | good (there's no layers file, so which layer may import which wasn't checked) |
| Deep modules, narrow doors | in places |
| One way per job | **poor** |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked |

Overall the code is small and the layering is clean: `app → checkout → cart/receipt/payments/notify/tax`. The structural cost is concentrated in two places, and both show up repeatedly in the history.

### Bugs found while reading (not structural, but these may come before any fix below)
- **Customers can be charged twice.** `shop/payments.py` `charge()` retries after timeouts and 502/503 errors without an idempotency key. If a charge succeeds but the response is lost, the retry charges the card again.
- **The receipt doesn't match the charge.** `checkout()` charges the total plus sales tax, but `render()` prints the total before tax. I ran an example: the customer is charged 100.95 and the receipt says 94.35.
- **Every member checkout from the command line crashes.** In `app.py` `main()`, the `--member` flag gets parsed as an item `sku=qty` and raises `ValueError`.
- **The tax category is hardcoded.** `checkout()` always passes `"general"`, so the food, clothing and books rates never apply.
- **East-region clothing tax depends on whether the amount is even.** 20000 cents is taxed at 6% and 20001 cents at 5%. Unknown regions silently get 7%.
- **Order emails can block checkout and fail silently.** `send_order_email()` can block for about 37 seconds after the card is already charged, and checkout ignores its failure result.

### Fix first, in order
1. **Merge the duplicated discount logic in `shop/cart.py` and `shop/receipt.py`** (weight 9). The two files changed together in 5 of 13 commits with no import between them. They drifted twice: commit 82b04a5 changed only the cart, and 716a01b, fa4e4f0 and 6c240fd were fixes for the copies disagreeing. That's 3 of the 4 fix commits that touched either file. Have the receipt call `cart_total()`. Skill: **untangle**.
2. **Use one HTTP client and one retry helper** (weight 8). Payments uses `http.client` and email uses `urllib.request`, and each has its own retry loop. Commits 1e77a42, 15edf68 and 1fd7dcc each fixed the same kind of retry/timeout bug in one copy only. A shared helper is also the natural place to add the idempotency key that fixes the double charge. Skill: **cleanup**.
3. **There is no third structural fix that has paid off.** The only other finding is the 61-line, deeply nested `sales_tax()` in `legacy/tax_tables.py`. Nothing has touched it since the 2019 port, so its shape has cost nothing so far. I'd put the double-charge fix third instead, or first if you're ranking by risk rather than by how much it slows down future changes. Fix 2 gives it a home.

Before you rely on `tests/test_totals.py`, check whether it actually catches broken code; that's what **verify-loop** does. It only compares the cart and receipt totals with each other, and it doesn't cover tax or payments.

I made no code changes. I deleted the scratch `.checkup/` and `__pycache__` folders, and `git status` is clean.