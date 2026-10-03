**The structure is wrong in two places. Fix `pricing/quote.py` first, because it is what stops the order flow running offline.**

I read the import graph across all of `fixture/` and opened the order-flow files. This is *traced*, not run. I didn't execute anything.

## Why nobody can run the order flow on a train

- **`pricing/quote.py:10-15` makes a live HTTP call in the middle of pricing.** `unit_price` calls `_fetch_margin()`, which hits `https://rates.example.internal/v1/margin` with a 2-second timeout. The call path is `place_order` → `build_lines` → `unit_price`.
  - Offline, it silently falls back to a margin of `1.0` after waiting on the timeout.
  - That means a laptop run is slow and quietly prices differently from production. Nothing in the code tells you this happened.
- **`api/routes.py:1,10` hardcodes `LiveGateway()`.**
  - `place_order` already takes the gateway as a parameter, which is the right design, and `payments/fake.py` already exists. The only place that picks a gateway is the route, and it always picks live.
  - Any test or local run that goes through the API therefore uses the live gateway.
- **State lives in module globals.** These are `PRODUCTS`, `ON_HAND`, `TRACK`, `OUTBOX` and `LOG`. You can't reset them between runs, and any test that touches them leaks into the next.

## Why changes touch too many files

- **`orders.status`, `shipping.tracking` and `notifications.email` form an import cycle.** `status` imports `tracking`, `tracking` imports `email`, and `email` imports `status`. It only loads because each uses `import x` and reads attributes later.
  - The cause is that `mark_delivered` sends the email directly, and `subject_for` reads order status. Shipping, notifications and orders each know about the other two, so a change to any one drags in the others.
- **`services/order_service.py` is a pass-through.** It is five lines that forward to `place_order` and add nothing. It does hide the fact that the real orchestration lives in `orders/place.py`.
- **`place_order` reaches into six modules directly.** It uses lines, inventory, tax, addresses, ids and shipping, and it hardcodes `500 * len(lines)` as the shipping estimate. Any change to pricing, tax or shipping rules lands in this one function.
- **The `core/util.py` grab-bag is over-imported.** `catalog/products.py`, `catalog/categories.py`, `catalog/images.py`, `catalog/search.py` and `customers/accounts.py` all import the same four helpers (`clamp`, `as_cents`, `slug`, `first`), and `products.py` uses only `slug`. This isn't harmful, but it makes it hard to see which imports are real dependencies.

## What to do first

1. **Make the margin lookup an injected dependency.** Give `unit_price` a margin provider, defaulting to the current HTTP fetch, and pass a constant `1.0` in tests and local runs. This is a small, reversible change to one file plus its callers in `orders/lines.py`. It is the smallest change that makes the order flow deterministic and offline.
2. **Choose the gateway from config in `api/routes.py`.** Use `fake.py` locally and `LiveGateway` otherwise. This is a few lines.
3. **Break the cycle by making `mark_delivered` return or emit an event.** The caller sends the email, so `tracking` no longer imports `notifications`. Do this after steps 1 and 2. It is the fix for changes touching too many files, but it is a larger refactor.

The check that steps 1 and 2 worked: `place_order` runs end to end with the network disabled, using the fake gateway and a fixed margin, and returns the same total each time. Nothing like that exists yet, so writing it is the first job.

I didn't open `inventory/`, `pricing/discounts.py`, `pricing/tax.py`, `reporting/` or `jobs/nightly.py` in full. I only saw their imports, so there may be more hidden coupling there. `jobs/nightly.py` imports the `ON_HAND` and `LOG` globals directly, which is worth a look next.