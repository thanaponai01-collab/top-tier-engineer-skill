# Checkup: `fixture/` shop

**What was measured:** 13 tracked files (12 of them code) and all 13 commits of history. Parsers covered 100% of the code. Two sections couldn't be measured. "Easy to find things" needs a `FEATURES.md`, and there isn't one. "Tests that can fail" means running the tests against deliberately broken code, which this checkup doesn't do.

## How well it's structured

| Property | Verdict |
|---|---|
| Easy to find things | not checked |
| One change in one place | **poor** |
| Dependencies point one way | good |
| Deep modules, narrow doors | in places |
| One way per job | in places |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked |

The layout is sensible overall: small modules, imports with no cycles, and no dead code. The real problem is the pricing rule. It exists twice, as two copies that nothing links, and the history shows it drifting again and again.

## Bugs found while reading the code

These are correctness problems, not structure, and I'd treat the first two as more urgent than any refactor:

- **`shop/payments.py` `charge()` can charge a customer more than once.** It resends the POST after a network error (including a timeout after the payment server has already taken the charge) and after 502/503 responses. There's no idempotency key, so one checkout can be charged up to 4 times.
- **`shop/checkout.py` `checkout()` produces a receipt that doesn't match the charge.** It charges the cart total plus tax, but the receipt it returns leaves the tax out. It also always passes the tax category `"general"`, so the food, clothing and books rates never apply.
- **`shop/receipt.py`** works out the total on its own instead of calling `cart_total()`, so the printed total can drift from what was charged.
- **`shop/cart.py` / `app.py`**: quantities aren't checked, so a negative quantity lowers the amount charged.
- **`shop/notify.py`**: if the order email fails, nothing notices, so a paid order can go unconfirmed without anyone knowing. It also waits once more after its last attempt for no reason.
- **`legacy/tax_tables.py`**: the east-region clothing rate depends on whether the amount in cents is odd or even, and an unknown region quietly gets 7%.

## What to fix first

The checkup found only **two** structural problems that the history shows costing real work:

1. **Merge the duplicated discount logic in `cart.py` and `receipt.py`.** The two files changed together in 5 commits with no import between them. In 82b04a5 the member discount changed only in the cart, and 716a01b had to fix the receipt afterwards. Commits fa4e4f0 and 6c240fd fixed rounding and bulk-discount mismatches between the copies. The receipt should call `cart_total()`; the tax-on-receipt fix fits in the same change. Skill: **untangle**.
2. **Make payments and emails use one HTTP client.** `payments.py` uses `http.client` and `notify.py` uses `urllib`, so retry, timeout and backoff were built twice and fixed twice (774a33f, 1e77a42 and 15edf68 in notify; a16bb3b and 1fd7dcc in payments). Skill: **cleanup**.

There was no third structural fix with a real cost. `legacy/tax_tables.py` `sales_tax()` is badly tangled, but it hasn't changed since it was ported in 2019, so today it costs no one anything.

**My recommended order for the quarter:**
1. Stop the double charge first: add an idempotency key, and only retry when the request is known not to have reached the server. Charging customers twice is a bigger risk than any structural problem.
2. Merge the cart and receipt logic, fixing the receipt tax at the same time.
3. Build the shared HTTP client, and move the payment retry fix into it.

I didn't change anything. The helper's scratch notes (`.checkup/`) are deleted, and `git status` is clean.