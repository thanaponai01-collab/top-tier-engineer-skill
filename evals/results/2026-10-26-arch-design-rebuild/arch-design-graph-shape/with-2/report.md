The structure is messy in places, not tangled. The order flow can't run on a train because pricing calls a remote service once for every order line, inside order placement. That's the place to start. The files-touched-per-change problem comes mostly from an import cycle and some copy-pasted helpers. I didn't change anything in `fixture/`. All the probes ran in throwaway copies, and the helper's final check confirms the repo is exactly as it was. There was no architecture doc in the repo to check against.

## Where it goes wrong

1. **Pricing makes a network call for each order line (I ran this).** `pricing/quote.py:19` calls `_fetch_margin()` (`quote.py:10-15`, which does an HTTP request with a 2-second timeout) every time a line is priced. It's reached through `orders/lines.py:6` from `orders/place.py:10`.
   - I placed a 3-line order with the network cut off: 3 HTTP calls, 6.0 seconds blocked. The wait grows by 2 seconds per line with no limit.
   - Worse, when the call fails the margin quietly becomes 1.0. So a laptop prices the same order differently from production, with no error.
2. **The order endpoint always uses the real payment gateway.** `api/routes.py:1,10` creates `LiveGateway()` directly. A fake gateway (`payments/fake.py`) and a shared interface (`payments/gateway.py`) already exist, but the API offers no way to use the fake without editing `routes.py`.
3. **Three modules import each other in a loop.** `orders/status.py:1` imports `shipping/tracking.py`, which imports `notifications/email.py:1`, which imports `orders/status.py` again. Changing an order's label or delivery message means editing all three packages together. It only loads because all three use `import pkg.mod`; switching any one to `from … import` would break it.
4. **Copy-pasted imports and repeated lookups.** 16 files import `core/util.py`. Five of them (`catalog/*`, `customers/accounts.py`) import all four of its names and use one at most. The customer's address is looked up in 3 places (`orders/place.py:11`, `shipping/rates.py:10`, `shipping/labels.py:6`), so changing the address rule touches 3 files.

## What to do first: fetch the margin once per order and pass it in

This mirrors how the order flow already handles payment, which comes in as a parameter (`place_order(..., gateway)`).

- **What changes:** `pricing/quote.py::unit_price`. It's used in two places, both in `orders/lines.py` (lines 1 and 6).
- **Steps** (behaviour stays the same after each one):
  1. Give `unit_price` an optional `margin=None`. When it's not given, fetch the margin exactly as today.
  2. In `build_lines`, fetch the margin once through a new public `pricing.quote.current_margin()` and pass it to every line. Three calls become one.
  3. Pass an optional `margin` through `place_order` and `build_lines`. `api/routes.py` still passes nothing and gets today's behaviour. Laptop runs and tests pass `margin=1.0` with `FakeGateway` and never touch the network.
  4. Once every caller passes a margin, make a failed fetch report an error instead of quietly using 1.0.
- **Proof:** this command runs from `fixture/`, places an order with the network blocked, and checks the total. It passes today (total 4427); rerun it after each step:
  ```
  python -B -c "import sys,urllib.request as u;sys.path.insert(0,'.');u.urlopen=lambda *a,**k:(_ for _ in ()).throw(OSError());from catalog.products import add_product;from inventory.stock import receive;from services.customer_service import register;from services.order_service import place;from payments.fake import FakeGateway;[(add_product(s,'I '+s,1000),receive(s,10)) for s in 'ABC'];a=register('<email>','1','T','US');o=place(a['id'],[{'sku':'A','qty':1},{'sku':'B','qty':2},{'sku':'C','qty':1}],FakeGateway(),'WELCOME10');print(o['total']);assert o['total']==4427,o['total']"
  ```
- **Risk:** low. It's an internal signature change, and undoing it means reverting one function signature.
- **Not doing:** caching the margin in the module or refreshing it in the background. That would still hide a network call inside pricing: a laptop would still hit the network on first use and still quietly fall back to 1.0. It would also add shared state and staleness rules to test.

## Bugs I noticed along the way (not structure)

- **Login doesn't verify anything.** `api/auth.py:5` takes whatever comes before the first `:` in the token as the customer ID. Anyone can place orders as any customer.
- **Stock isn't returned when something fails.** `orders/place.py:14-16` reserves stock line by line and then charges. If a later line is out of stock, the earlier lines stay reserved. If the charge fails, nothing is released.
- **An unknown token crashes the endpoint.** `api/routes.py:10` reads `acct['id']` without checking it exists, so an unknown token causes a `TypeError` instead of an error response.

Which one should we look into further: the margin change above, letting the endpoint use the fake gateway (finding 2), or breaking the import loop (finding 3)?