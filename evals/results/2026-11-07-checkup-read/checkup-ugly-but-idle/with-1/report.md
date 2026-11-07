# Checkup of the shop in `fixture/`

The codebase is small: 12 code files and 13 commits. Most of it is laid out sensibly. Imports run one way, network I/O is limited to `payments.py` and `notify.py`, and the checker found no dead code. Almost all the pain sits in two places. The checkup gate passed (`CHECKUP-GATE: done`). I changed nothing and deleted the `.checkup/` scratch notes afterwards.

| Property | Rating |
|---|---|
| Easy to find things | not checked (there's no feature map) |
| One change in one place | **poor** |
| Dependencies point one way | good (imports only; there's no `layers.txt`, so layer rules weren't checked) |
| Deep modules, narrow doors | in places (`legacy/tax_tables.py` is tangled, but nobody has changed it since it was ported) |
| One way per job | **poor** |
| Logic apart from I/O | good |
| No dead code | good |
| Tests that can fail | not checked (that needs the tests run against broken code; verify-loop does this) |

## Three things to fix first, in order

**1. A payment can be charged twice.** `shop/payments.py` `charge()` resends the POST after a timeout or network error and after a 502/503. It has no idempotency key, so the payment provider can't tell a retry from a new charge. If the provider had already taken the first one, the customer pays twice. This is a bug rather than a structure finding, but it's about money, so I'd put it ahead of everything else.

**2. The discount rule is copied in two files: `shop/cart.py` and `shop/receipt.py`.** This is the change that has cost the most so far, and the checkup ranks it first among the structural findings.
- Nothing links the two copies. They changed together in 5 commits, and 3 of those were fixes for the copies drifting apart:
  - **`716a01b`:** fixed the receipt after `82b04a5` changed only the cart.
  - **`fa4e4f0`:** the two copies rounded differently.
  - **`6c240fd`:** both showed the wrong bulk percentage.
- On top of that, `checkout()` charges the cart total **plus sales tax**, but the receipt it returns leaves the tax out. Customers see a lower total than they paid.
- The fix: work out the total in one place, and have the receipt use that number, tax included.
- Tool for it: untangle.

**3. Each network module writes its own HTTP retry loop.** `payments.py` uses `http.client` and `notify.py` uses `urllib`. Every retry problem has been found and fixed separately in each file:
- **notify:** timeout (`1e77a42`), then no backoff (`15edf68`).
- **payments:** leaked connections (`1fd7dcc`).

One shared helper for requests and retries, with backoff and timeouts, would fix this. It's also the natural place to add the idempotency key from fix 1. Tool for it: cleanup.

## Other problems found while reading (smaller)
- **Slow email can hold up checkout:** `send_order_email()` runs inside checkout after the charge and can block it for about 37 seconds. If it fails, nothing reports it.
- **Tax category is hard-coded:** `checkout()` always passes `"general"`.
- **Odd tax rule:** `sales_tax()` gives east-region clothing 1% less tax when the amount in cents is odd, and any unknown region quietly gets 7%. Ask whoever owns tax whether that's intended.
- **Crashes on bad input:** `app.py` `main()` shows a traceback for an unknown SKU or a missing argument instead of an error message.

## What to leave alone
I'd leave the tangled `legacy/tax_tables.py` for now. Only the first commit ever touched it, so its tangle isn't costing anything yet. Check the odd tax rule above with whoever owns tax, though.