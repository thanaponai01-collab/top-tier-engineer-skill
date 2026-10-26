I read all 53 files (431 lines) and ran the order flow against the fake gateway. The main problem is that the domain code reaches out to other modules and to the network directly, when those things should be passed in. That is behind both of your problems.

## What to do first: stop `unit_price` from calling the network

`pricing/quote.py:18-20`: every call to `unit_price` makes an HTTP request (`_fetch_margin()` → `rates.example.internal`). `build_lines` calls it **once per order line**. That breaks offline use in two ways:

- **It slows down or hangs.** Each line can wait up to 2 seconds for the timeout. When I ran it, DNS failed quickly and a 2-line order finished in 0.06s. On flaky train Wi-Fi or a captive portal, it will hit the timeout on every line.
- **It gives wrong prices without saying so.** The `except OSError: return 1.0` fallback means offline orders are priced with no margin. My test order came to 3760 cents, which is the base price plus tax and shipping. You can't trust anything you check on a laptop, and the same thing would happen in production if the rates service went down.

The fix already exists in the codebase. Payments do this correctly: `PaymentGateway` is a Protocol, `FakeGateway` exists, and `place_order` takes the gateway as a parameter. Do the same for margin:

- Add a `MarginSource` protocol with live and fixed implementations.
- Fetch the margin **once per order** in `place_order` and pass it down to `build_lines` / `unit_price`.
- Let failures raise errors instead of falling back to 1.0.

The second part of the fix is in `api/routes.py:1,10`, which hard-codes `LiveGateway()`. Wire the gateway and margin source in one place, from config, so a local run can use fakes for both.

## Why changes touch too many files

**1. An import cycle that hides how coupled things are.**
`orders.status` imports `shipping.tracking`, which imports `notifications.email`, which imports `orders.status`. The cycle only works because those three files use `import x.y` instead of `from x import y`; with `from` imports it would crash at load time. Two things cause it:
- `tracking.mark_delivered` sends an email itself (`shipping/tracking.py:10`). Shipping shouldn't know notifications exist.
- `email.subject_for` reaches back into `orders.status.label`.

Fix: have `mark_delivered` return or publish a "delivered" event, and let the caller (a service) send the notification. Pass the label text into `subject_for` instead of importing it.

**2. The "customer's country" lookup is repeated.**
`orders/place.py:11` works out the country from `default_address(cid)`. Then `quote_shipping(cid, …)` (`shipping/rates.py:10`) looks up the same address again from `cid`, and `shipping/labels.py` does it a third time. Any change to how addresses work means editing orders, shipping rates and labels. Fix: `place_order` should resolve the address once and pass the country or address into shipping, so shipping no longer imports `customers`.

**3. Modules edit each other's data directly.**
- `inventory/reserve.py` changes `stock.ON_HAND` directly.
- `jobs/nightly.py` reads `orders.history.LOG` and `inventory.stock.ON_HAND`.

Every module keeps its data in a module-level dict (`ACCOUNTS`, `PRODUCTS`, `ON_HAND`, `LOG`, `TRACK`, …), so the storage format is effectively a public API. Changing how any of it is stored breaks the code that reads it. Fix: give each module functions for this (`stock.decrement`, `history.count`, `stock.sku_count`), and later move the stores into objects that get passed in. That also lets tests start from a clean state instead of sharing globals.

**4. Unused imports make modules look more connected than they are.**
`from core.util import clamp, as_cents, slug, first` is copied into four catalog/customer files that use one of those names or none. Other unused imports:
- `as_cents` in `api/schemas.py`
- `lines_total` in `orders/status.py` and `reporting/sales.py`
- `add` in `reporting/sales.py`
- `chunks` in `reporting/exports.py`
- `slug` in `notifications/templates.py` and `shipping/labels.py`
- `clamp` in all three inventory files

The result is that `core/util` looks like it's used everywhere, and the dependency graph points at the wrong places. `core/util.as_cents` and `core/money` also overlap. Deleting the unused imports is cheap and makes the real dependencies visible.

**5. A layer that only passes calls through.**
`services/order_service.place` just forwards to `orders.place.place_order` with the same arguments, so it's one more file to edit with every signature change. Either give it the coordination role (resolve the address, fetch the margin, choose the gateway, record history, send notifications) or delete it.

## Bugs I noticed (not structural)
- `place_order` reserves stock before charging. If the charge fails, or the third line's `reserve` raises, the reservations already made are never released.
- `orders.history.record` is never called, so the nightly job's `events` count is always 0.
- Shipping weight is `500 * len(lines)`, so quantity is ignored.

## Suggested order
1. Inject the margin source and choose fakes in one place: this fixes running offline.
2. Delete the unused imports: about an hour of work, and the dependency graph becomes accurate.
3. Break the orders → shipping → notifications cycle.
4. Pass the address into shipping.
5. Hide the global stores behind functions.

Doing 3 and 4 together with the `order_service` change makes it the one place that coordinates an order, which is the main thing this codebase is missing. I haven't changed any files. Tell me if you want me to start on step 1.