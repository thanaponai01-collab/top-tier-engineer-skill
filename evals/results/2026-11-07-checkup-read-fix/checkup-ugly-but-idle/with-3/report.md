I ran the checkup on 13 tracked files and all 13 commits. All four stages passed (`CHECKUP-GATE: done`). I changed nothing: the `.checkup/` scratch notes are deleted and `git status` is clean.

## How well it's structured

| Property | Rating | Why |
|---|---|---|
| Easy to find things | not checked | There's no FEATURES.md mapping features to code |
| One change in one place | **poor** | The discount rules are copied in `cart.py` and `receipt.py` |
| Dependencies point one way | good | No findings (layer rules weren't checked because there's no `layers.txt`) |
| Deep modules, narrow doors | in places | `legacy/tax_tables.py:4` `sales_tax()` is long and tangled (complexity 25, nested 9 deep) |
| One way per job | in places | HTTP calls use two libraries: `http.client` in payments, `urllib` in notify |
| Logic apart from I/O | good | — |
| No dead code | good | — |
| Tests that can fail | not checked | Checking needs the tests run against deliberately broken code (verify-loop does that) |

Overall: it's small and the layering is sound. The cost is in duplicated rules, which show up as a steady run of "fix" commits.

## Bugs found while reading (not measured or reproduced)
These came from reading the code. I didn't run anything to confirm them.
- **`shop/payments.py` `charge()` can charge a customer twice.** It retries the POST after a timeout or a 502/503 without an idempotency key, so a charge the server already accepted can be sent again.
- **`shop/receipt.py` `render()` prints a total without sales tax.** `checkout()` charges the cart total plus tax, so in any taxed region the receipt shows less than was charged.
- **Failed order emails go unnoticed.** `checkout()` ignores the result of `send_order_email()`, so a paid order can get no confirmation and nobody hears about it.
- **Smaller issues:**
  - `app.py` doesn't check its arguments; bad input crashes.
  - `sales_tax()` silently charges unknown regions 7%.
  - The east-region clothing rate depends on whether the price in cents is even.
  - Tax is always worked out for the category `"general"`.

## Fix first, in order
Only two findings have a measured cost in the history. My third pick, ranked first, is a bug from the read rather than a structure finding.

1. **Make `charge()` safe to retry.** Send an idempotency key, and don't blindly resend the POST after a read timeout. This isn't a structure issue, but sending a customer's payment twice is the most expensive thing in the code.
2. **Keep the discount rules in one place.** `cart.py` and `receipt.py` changed together in 5 commits with no link between them, and drifted three times:
   - `82b04a5` changed only the cart, and `716a01b` then had to fix the receipt to match.
   - `fa4e4f0` fixed rounding that differed between the two.
   - `6c240fd` fixed a wrong bulk discount in both.

   `receipt_total` should call `cart_total` (or both should share one rule set), and the receipt should print the amount actually charged, tax included. That also fixes the receipt-total bug above. The `untangle` skill does this kind of fix.
3. **Use one HTTP helper with shared retry and timeout handling.** Retry, timeout and backoff were written and fixed separately in each file: `774a33f`, `1e77a42` and `15edf68` in notify; `a16bb3b` and `1fd7dcc` (a connection leak) in payments. The `cleanup` skill does this.

I'd leave `legacy/tax_tables.py` alone for now. It's ugly, but nothing has touched it since the first commit. Before relying on the tests, run verify-loop to see whether they can actually fail.