## Checkup: the shop in `fixture/`

**What was measured:** 13 tracked files (12 of them code) and all 13 commits. The structure, dependency-graph and duplication checks all ran, and their parser read 100% of the code. Two sections couldn't be measured. "Easy to find things" needs a FEATURES.md, which the repo doesn't have. "Tests that can fail" means running the tests against deliberately broken code, which a checkup doesn't do.

### How well it's structured

| Property | Verdict |
|---|---|
| Easy to find things | not checked |
| One change in one place | **poor** |
| Dependencies point one way | good (there's no layers file, so layer rules weren't checked) |
| Deep modules, narrow doors | in places |
| One way per job | in places |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked |

The layout is small and sensible. Network calls are kept in `payments` and `notify`, and there are no import cycles or dead code. The weak spot is duplication: the same rules are written out in more than one place, and the commit history shows it keeps causing bugs.

### Bugs I found reading the code (deal with these before or alongside the fixes)
I found these by reading the code. I didn't run anything.
- **Customers can be charged twice.** `shop/payments.py` `charge()` resends `POST /charge` after a 502/503 or a network error, including a timeout after the request was already sent. There's no idempotency key, so the payment provider can't tell a retry from a new charge.
- **The receipt total is lower than the amount charged.** `checkout()` charges the cart total plus sales tax, but `render()` prints the total without tax.
- **Product-specific tax rates never apply.** `checkout()` always passes `"general"` as the category to `sales_tax()`, so the food, clothing and books rates are never used.
- **The `--member` flag crashes the app.** `app.py` treats every argument after the region as `sku=qty`, so a trailing `--member` (as the README shows) raises `ValueError`. An unknown sku raises `KeyError`.
- **Email failures are mishandled.** `notify` retries 4xx errors that will never succeed, and `checkout()` ignores whether the email was sent.
- **One tax rule looks like a porting mistake.** In the east region, the clothing rate depends on whether the amount in cents is even.

### Fix first, in order
1. **Put the discount rule in one place: `shop/cart.py` and `shop/receipt.py`.** `cart_total()` and `receipt_total()` each have their own copy of the discount constants and maths. The two files changed together in 5 of the 13 commits. Two of those were fixes for the copies drifting apart: 716a01b (82b04a5 changed only the cart) and fa4e4f0 (they rounded differently). 6c240fd then had to fix the same wrong percentage in both. The receipt should use the cart's calculation. Skill: **untangle**.
2. **Write the HTTP retry logic once.** `payments` uses `http.client` and `notify` uses `urllib.request`, and each has its own retry, timeout and backoff code. Each module had to learn the same lessons separately: 1e77a42 and 15edf68 fixed timeouts and missing backoff in notify, and 1fd7dcc fixed leaked connections in payments. A single shared helper is also the right place to fix the double charge (an idempotency key, and no resend once the request has gone out). Skill: **cleanup**.
3. **Untangle `legacy/tax_tables.py` `sales_tax()` before changing tax.** It's 61 lines, complexity 25, nested 9 deep and untested. It hasn't changed since the first commit, so it costs nothing today. But fixing the hardcoded `"general"` category is the obvious next tax change, and that work lands in this function. Turn it into a table and add tests first. Skill: **arch-design**.

Nothing in the repo was changed. The checkup's scratch folder (`.checkup/`) was deleted afterwards, and `git status` is clean.