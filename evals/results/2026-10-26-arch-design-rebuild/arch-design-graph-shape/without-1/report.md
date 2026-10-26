## Short answer

Two problems cause most of the pain. Pricing makes a hidden network call partway through the order flow. And the orders, shipping and notifications packages import each other in a loop. Fix the pricing call first, because that's the one blocking offline work, and the codebase already shows how to do it.

## 1. A hidden network call inside pricing (the train problem)

`pricing/quote.py:10-19`: `unit_price()` calls `urllib.request.urlopen(RATES_URL)` on every line item. Nothing in the call chain shows this. The route calls `services.place`, which calls `orders.place_order`, then `orders.lines.build_lines`, then `unit_price`, and only there does the network call happen. You can't pass in a replacement, so the only way around it is monkeypatching.

I ran `place()` with `FakeGateway` on this machine. It finished in 0.08s because DNS for `rates.example.internal` failed quickly, and the code then quietly fell back to a margin of `1.0`. So offline:

- **Prices are silently wrong.** There's no error, just different totals from production.
- **Bad networks are worse than no network.** I didn't test this, but it follows from the code. On a slow connection each line can wait up to 2s. Behind a captive portal (common on trains), `float(r.read())` gets HTML back and raises `ValueError`, which `except OSError` doesn't catch, so the order flow crashes.
- **Each order makes one call per line.** This is the same value fetched N times.

The fix is already in the repo. Payments do it properly: there's a `PaymentGateway` protocol in `payments/gateway.py`, plus `LiveGateway` and `FakeGateway`, and the gateway is passed in. Pricing should work the same way:

- Fetch the margin once per order, or put it behind a `MarginSource` with a live version and a fixed one.
- Pass it in through `place_order` and `build_lines`.
- Choose the live or fixed version where `routes.py` already chooses `LiveGateway`.

That makes the order flow fully runnable offline, with honest prices.

## 2. An import cycle: orders → shipping → notifications → orders

- `orders/status.py` imports `shipping.tracking` (for `eta_text` in `label`).
- `shipping/tracking.py` imports `notifications.email` (`mark_delivered` sends the email).
- `notifications/email.py` imports `orders.status` (`subject_for` calls `label`).

It only loads because these three files use `import a.b` instead of `from a.b import x`, which delays the lookup until the function is called. That style appears only in these three files, which suggests someone hit the circular-import error and worked around it. The result is that changing any one of the three can break the others.

To fix it, have tracking report the delivery (return it or emit an event) and let the caller send the email. Have `email` take the subject text as an argument instead of building it from `orders.status`.

## 3. Why changes spread to more files than they should

- **A pass-through service layer.** `services/order_service.py` only forwards to `orders.place.place_order`. Adding one parameter means editing `place.py`, `order_service.py` and `routes.py`. Either give the layer a real job (this is a natural home for the margin and gateway wiring from item 1) or delete it. `customer_service.py` does coordinate several steps, so it can stay.
- **Copy-pasted `core.util` imports.** Five modules have `from core.util import clamp, as_cents, slug, first` and use one name from it or none. About ten modules import things they never use, for example `search.py`, `accounts.py`, `schemas.py`, `reserve.py`, `stock.py`, `templates.py`, `exports.py`, `labels.py`, and `lines_total` / `add` in `reporting/sales.py` and `orders/status.py`. That makes everything look dependent on `util`. `util` also overlaps with `core/money.py` (`as_cents` is in `util`).
- **Shipping depends on customers.** `shipping/rates.py` and `labels.py` take a `cid` and look up `default_address` themselves, and `orders/place.py` looks up the same address too. They should take a country or address as an argument, so a change to the address model only touches `customers` and `orders`.
- **Other modules use another module's dicts directly.** `inventory/reserve.py` edits `stock.ON_HAND` directly, and `jobs/nightly.py` reads `orders.history.LOG` and `inventory.stock.ON_HAND`. Any change to how that data is stored breaks those callers. Add small accessor functions (`count_events()`, `sku_count()`, `stock.take()`).

## 4. Related correctness issue in `place_order`

`orders/place.py:15-17` reserves stock before charging, with no rollback. If `gateway.charge` fails, the stock stays reserved. This becomes easier to test once item 1 is done.

## Recommended order

1. **Pass the pricing margin in** (item 1). It's a small change that follows the gateway pattern, it lets people run orders offline, and it removes the silent price drift.
2. **Break the orders/shipping/notifications cycle.**
3. **Clean up:** fold the margin and gateway wiring into `order_service` or drop the layer, remove unused `core.util` imports, pass addresses into shipping, and add accessors for shared state.

I didn't change any files.