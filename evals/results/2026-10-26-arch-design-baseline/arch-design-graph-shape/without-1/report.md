The order flow has two seams it needs. Payments has one. Pricing doesn't, and its network call is what stops anyone running the order flow offline. Separately, three structural habits explain why changes spread across so many files. Fix the pricing seam first.

## 1. Why the order flow won't run offline (fix this first)

**`pricing/quote.py:10-20`** makes a network call to a hard-coded URL inside `unit_price()`, once for every order line:

```python
def unit_price(sku, code=None):
    cents = scale(base_price(sku), _fetch_margin())   # urllib.urlopen(RATES_URL, timeout=2)
```

- On a train, each line can hang for the 2s timeout plus however long the DNS lookup takes. The timeout doesn't cover DNS.
- When it fails it quietly uses a margin of `1.0`. So offline prices come out different from production prices with no warning. I ran `place_order` here and got a "valid" total of 2126 at margin 1.0, with no sign the margin was a fallback.
- Nobody can swap this out without monkey-patching `urllib`.

The pattern to copy already exists in the codebase. `payments/` has a `PaymentGateway` Protocol plus `FakeGateway` and `LiveGateway`, and `place_order` receives the gateway as a parameter. Give margin the same treatment:

- A `MarginSource` protocol with `HttpMarginSource` and `FixedMarginSource(1.0)` implementations.
- Fetch the margin once per order, not once per line, and pass it into `build_lines` / `unit_price`.

The other half of the problem is **`api/routes.py:1,10`**, the only entry point. It creates `LiveGateway()` directly, so the HTTP path can never run with the fake. Move the choice of gateway and margin source into one composition function driven by config (`APP_ENV=local` → fakes). That gives you a laptop mode with one switch. A small `dev_seed.py` would help too: today the catalog and stock start empty, so `base_price` raises `KeyError` until someone adds products and stock by hand.

## 2. Why changes touch too many files

**a. An import cycle hidden by module-style imports.**
`orders/status.py` → `shipping/tracking.py` → `notifications/email.py` → `orders/status.py`.
Each of those files uses `import x.y` rather than `from x.y import z`, which is the usual workaround for circular import errors. The causes are:
- `shipping.tracking.mark_delivered` sends email directly (`tracking.py:10`).
- `orders.status.label` asks shipping for an ETA.
- `notifications.email.subject_for` formats order status.

A change to any one of the three can break the other two. To fix it, have `mark_delivered` return or publish a "delivered" event and let the caller (or a small handler) send the notification. Move `subject_for` out of `notifications` so that notifications only renders templates.

**b. Shipping looks up the customer's address itself, in three places.**
`orders/place.py:11`, `shipping/rates.py:10` and `shipping/labels.py:6` each call `default_address(cid)` and default the country (`'US'` in two of them). `place_order` already has the country, then calls `quote_shipping(cid, ...)`, which looks it up again. Change `quote_shipping(country, weight_g)` and `label_text(address, order_id)` to take plain values. Shipping then no longer depends on `customers`, and changes to the address model only touch `customers` and the order code that calls it.

**c. Every module reaches into other modules' storage.**
Each package keeps its data in a module-level dict or list (`PRODUCTS`, `ON_HAND`, `LOG`, `ACCOUNTS`, …), and other packages read and write those directly:
- `inventory/reserve.py:8` modifies `stock.ON_HAND`.
- `catalog/search.py:1` iterates over `products.PRODUCTS`.
- `jobs/nightly.py:2-3` reads `orders.history.LOG` and `inventory.stock.ON_HAND`.

Moving any of this to a real store means editing every reader. Put access behind functions inside the owning package, with `jobs` and `reporting` going through those functions. Done thoroughly, that becomes a per-package repository object you can pass in, which also makes tests independent of each other.

Orders have the same problem in a different form. An order is a plain dict whose keys (`'total'`, `'lines'`, `'qty'`, `'status'`) are known to `api/schemas`, `reporting/sales`, `notifications` and `orders/status`. A small `Order` dataclass in `orders/` would mean a change to the order's shape only touches `orders/`.

## 3. Smaller issues

- **Imports copied and pasted from `core.util`.** `from core.util import clamp, as_cents, slug, first` appears in 5 catalog/customers files that mostly use one of those names or none (`search.py` and `accounts.py` use none). There are also unused imports in `api/schemas.py`, `orders/status.py` (`lines_total`), `reporting/sales.py` (both imports), `reporting/exports.py`, `inventory/*`, `notifications/templates.py` and `shipping/labels.py`. They make the dependency graph look denser than it is, and renaming anything in `core.util` touches a dozen files. Run a linter (`ruff --select F401`) to remove them. Also, `as_cents` belongs in `core/money.py`, not in the grab-bag `util.py`.
- **`services/order_service.py` only forwards the call to `orders.place.place_order`.** It's one more file to edit on every signature change and does nothing. Either remove it, or make it the composition point from section 1 (that would give it a real job).
- **A correctness bug in the same function, worth fixing while you're in there.** `place_order` (`orders/place.py:14-16`) reserves stock line by line, then charges. If a later line is short of stock, or the charge fails, the earlier reservations are never released. The order history (`orders.history.record`) is also never written.

## Recommended order

1. Add the margin port, fetch the margin once per order, and choose gateway and margin source in a config-driven composition root. That unblocks offline runs and makes prices deterministic in tests.
2. Run the unused-import cleanup. It's cheap and shows the real dependency graph.
3. Break the orders → shipping → notifications cycle.
4. Make shipping take an address or country instead of a customer id.
5. Gradually put module state behind functions or repositories, and introduce an `Order` type.

I checked the hidden-fallback behaviour by running `place_order` with `FakeGateway` here: the margin fetch failed fast and the price used 1.0. On a network that is up but flaky, expect the per-line timeout waits instead. I haven't changed any code.