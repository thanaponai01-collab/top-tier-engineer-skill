The biggest problem is that pricing secretly calls the network. The second is a three-package import cycle running through order status, shipping and notifications. Fix the pricing call first: it's the direct cause of the "can't run it on a train" complaint, and it's a small change.

## 1. Pricing makes a network call for every line item (the offline problem)

`pricing/quote.py:10-20`: `unit_price()` calls `_fetch_margin()`, which does an HTTP request to `rates.example.internal`. `orders/lines.py:6` calls `unit_price` once per item, so placing one order makes N network calls from deep inside `place_order`. You can't see this from the API, the service or the order code.

I ran `place_order` with three items and the `FakeGateway`:

```
network calls: 3   elapsed 0.05s   total 3785
```

It failed quickly here because DNS lookups fail immediately on this machine. On patchy train wifi or behind a login page, each line can wait the full 2s timeout or longer, because DNS lookup isn't covered by `timeout=`. There's also a correctness problem: `except OSError: return 1.0` quietly prices at margin 1.0 whenever the service is unreachable. That happens in production too, with no log or error.

The fix already exists in this codebase. `payments/` does it right: a `PaymentGateway` Protocol (`payments/gateway.py`), a `FakeGateway`, a `LiveGateway`, and the gateway passed into `place_order`. That's why payments is not the reason the flow can't run offline. Pricing should copy that pattern:

- Add a `MarginSource` protocol with a live (HTTP) version and a fixed version.
- Fetch the margin once per order in `place_order` (or the service layer) and pass it to `build_lines` / `unit_price`.
- Choose live or fixed in `api/routes.py`, which already chooses `LiveGateway`.
- Make the silent `1.0` fallback either fail loudly or log, and decide which on purpose.

That's about four files, and after it the whole order flow runs with no network.

## 2. Import cycle: orders → shipping → notifications → orders

- `orders/status.py:1` imports `shipping.tracking` so that `label()` can show an ETA.
- `shipping/tracking.py:1` imports `notifications.email` so that `mark_delivered()` sends an email.
- `notifications/email.py:1` imports `orders.status` so that `subject_for()` can call `label()`.

All three use `import pkg.mod` rather than `from ... import`. That's the usual trick for getting a cycle past Python's import rules: it works, but it hides the cycle. This loop is why changes spread across files. Change how status labels work and you're editing in orders, shipping and notifications together.

To break it:
- Tracking should record delivery and return. Whatever calls it (a service or job) then sends the notification.
- `subject_for` should take the label as a string instead of importing `orders.status`.

## 3. Shipping looks up the customer's address again

`orders/place.py:11` already works out `country` from `default_address(cid)`. Then `shipping/rates.py:9-10` takes `cid` and calls `default_address` again. `shipping/labels.py` does the same. So shipping depends on `customers`, and a change to the address format reaches into shipping. Pass `country` (and the address) in: `quote_shipping(country, weight_g)`.

## 4. Dependencies that don't actually exist

- `from core.util import clamp, as_cents, slug, first` is pasted into 5 files, which mostly use none of those names (all of `catalog/*` and `customers/accounts.py`).
- More unused imports: `reporting/sales.py:1-2` (`lines_total`, `add`), `orders/status.py:2`, `reporting/exports.py:2`, `api/schemas.py:1`, `notifications/templates.py:1`, `shipping/labels.py:1`, and `inventory/*` (`clamp`).

These make the dependency graph look denser than it is. For example, reporting appears to depend on `orders.lines`. Anyone checking "what touches this?" gets wrong answers. A linter (ruff `F401`) removes them all in one change. Also, `as_cents` is money logic sitting in `core/util` instead of `core/money`, and `util` is a grab-bag that will keep growing.

## 5. Smaller structural issues (later)

- **`services/` is inconsistent.** `customer_service.register` does real coordination. `order_service.place` is a one-line pass-through (`services/order_service.py:4-5`), so every change to `place_order`'s signature touches two files for no benefit. Make the order service the real coordinator: it's the natural place for the margin fetch, the address lookup and the post-delivery notification from items 1–3. Then `orders/place.py` can stay pure domain logic.
- **Other modules read and write each other's data directly.** Every package keeps state in module-level dicts, and other modules reach into them: `jobs/nightly.py` reads `orders.history.LOG` and `inventory.stock.ON_HAND`, `catalog/search.py` reads `PRODUCTS`, and `inventory/reserve.py` changes `ON_HAND` directly. That's fine for now, but any future move to a database will spread through all of these. Put reads behind functions in the owning module.
- **`place_order` has no rollback** (`orders/place.py:14-16`). If the second `reserve` raises, the first reservation is never released. If `gateway.charge` fails, all the reservations leak. This is a correctness bug, not a structure problem, but it lives in the code you'll be touching for item 1.

## Recommended order

1. **Put the margin source behind an injected interface, like payments does.** This makes the order flow run offline and makes the silent mispricing visible.
2. **Break the orders/shipping/notifications cycle** by moving the delivery email out of `shipping.tracking`.
3. **Pass `country` into shipping** instead of `cid`, and give `order_service` the coordination work.
4. **Turn on an unused-import lint** so the dependency graph shows the real dependencies.

I haven't changed anything in `fixture/`. Item 1 is small enough to do now if you'd like.