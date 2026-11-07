## Overall

The structure is mostly fine. It's a small codebase (about 210 lines) with sensible module boundaries: catalog, cart, receipt, checkout, payments, notify, plus a legacy tax module. `checkout.py` is a clean place where everything comes together. The problem is not the layout. It's that a few pieces of logic exist in two places, and the git history shows that's where the bugs keep coming from.

Of the 12 commits after the initial one, 9 are features or fixes in just two areas:
- **Discount logic** (`cart.py` and `receipt.py`): 6 commits, 3 of them "receipt doesn't match cart" fixes (`716a01b`, `fa4e4f0`, `6c240fd`).
- **Retry logic** (`payments.py` and `notify.py`): 5 commits, and each retry feature needed a follow-up fix (`1fd7dcc`, `1e77a42`, `15edf68`).

`legacy/tax_tables.py` looks the worst, but it hasn't changed since the initial commit. The 2 existing tests pass.

## Fix first, in order

**1. Calculate the order total once, and print the amount you actually charged.**
`shop/cart.py:3-15` and `shop/receipt.py:3-24` are copies of the same discount code. They have the same constants, and every pricing change has had to be made twice. Missing one copy is how the three drift bugs happened. Worse, the receipt is wrong even when the two copies agree:
- `checkout.py:9-10` charges the cart total plus sales tax.
- `render()` prints `receipt_total`, which has no tax in it.

Example: 3 tees and 2 caps for a member in "north" gets charged $100.95, but the receipt says $94.35. The fix is to have checkout compute one total (subtotal, discount, tax, final), pass it to both `charge()` and `render()`, and delete `receipt_total`. The existing test `test_receipt_matches_cart` only checks that the two copies agree, so it can't catch this.

**2. Make payment retries safe from double charges.**
`shop/payments.py:10-20` retries up to 4 times on `OSError` and on 502/503 responses. A read timeout counts as an `OSError` and happens *after* the request was sent, and a 502 from a gateway can arrive after the charge already went through. In both cases the customer may already have been charged, and there's no idempotency key, so a retry can charge them again. Fix: send a stable idempotency key (the order ID, for example) if the payment provider supports one. Also only retry blind on errors where the request clearly never got through, and pull the retry loop into one shared helper so payments and notify stop being patched separately.

**3. Take the order email off the checkout path.**
`checkout.py:13` sends the email synchronously and ignores the result. The customer waits through up to 3 × 10s timeouts plus backoff (about 37s at worst) after they've already paid, and a failed email is silently dropped. Fix: put the email on a queue or outbox (even a simple table plus a worker), and log or record failures. It can use the same retry helper as item 2.

## Not now
- **`legacy/tax_tables.py`** is messy. There's an odd parity rule for east-region clothing at `:42`, and since checkout always passes the category `"general"`, most of the branches never run. But it has never been touched, so it isn't costing you anything yet. When someone does need to change it, write tests that pin down its current behaviour first, then refactor.
- **Tests:** there are only 2, and none cover checkout, tax, payments or notify. Add tests alongside each of the three fixes rather than as a separate project.
- **Small things:** `catalog.py` throws a bare `KeyError` on an unknown SKU. `app.py` prints "payment failed" for any failure, and has no input validation.

I haven't changed anything in the repo.