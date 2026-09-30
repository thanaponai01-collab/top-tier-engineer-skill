**The order flow can't run offline because `pricing/quote.py` makes a live HTTP call inside price calculation, and changes touch too many files because ordinary logic is spread across many thin, tangled modules.** I read the imports of every file and the order-flow files themselves. I haven't run anything, so these are *traced*, not *proven*.

## Where the structure goes wrong

1. **Hidden network call in the pricing path (this is the train problem).**
   - `pricing/quote.py:10` `_fetch_margin()` calls `urllib.request.urlopen("https://rates.example.internal/...", timeout=2)`.
   - The chain is `place_order` → `build_lines` → `unit_price` → `_fetch_margin`, so every order attempts that fetch.
   - Offline, it falls back to `1.0` after up to 2 seconds per line. The code doesn't fail, but it is slow and the price is silently wrong.
   - The payment gateway is handled correctly: `PaymentGateway` is a Protocol, `FakeGateway` exists, and `place_order` takes the gateway as a parameter.
   - The margin fetch has no equivalent seam.
   - The fake gateway can't be used by `api/routes.py`, because `post_order` hard-codes `LiveGateway()`. The API path therefore can't run offline either.

2. **Import cycle: `orders.status` → `shipping.tracking` → `notifications.email` → `orders.status`.**
   - `label()` needs the ETA from tracking.
   - `mark_delivered()` sends an email.
   - The email's `subject_for()` needs the order label.
   - Fixing the tracking or email code means understanding all three modules.

3. **Global mutable state shared across packages.**
   - `inventory.stock.ON_HAND` is imported and mutated directly by `inventory/reserve.py` and `jobs/nightly.py`.
   - `orders.history.LOG` is imported directly by `jobs/nightly.py`.
   - `catalog.products.PRODUCTS` is a module global, and `pricing.quote` reads it through `base_price`.
   - There is no explicit store, so tests can't get isolation without resetting module state, and any change to a data shape reaches every file that imports it.

4. **`place_order` does everything inline (`orders/place.py`).**
   - It prices, looks up the address, computes tax and shipping, reserves stock, charges, and builds the record.
   - Reservations aren't rolled back if `gateway.charge` fails. That is a correctness gap, and I only read it, so it is *traced*.
   - The `services/order_service.py` wrapper only forwards the call, so it adds a file without adding a boundary.

5. **Copy-pasted imports.**
   - `catalog/{products,categories,images,search}.py` and `customers/accounts.py` all import `clamp, as_cents, slug, first` from `core.util`, and most don't use them.
   - This is unused import noise that makes `core.util` look like a dependency of everything.
   - It is minor, and I'd leave it for later.

## What to do first

Make the margin rate an injected dependency. It is one small change and fixes the offline problem.

- Give `unit_price` and `build_lines` a `margin` argument, or a `rates` provider like the gateway Protocol.
- Have `place_order` receive it the same way it receives `gateway`.
- Only `api/routes.py` wires in the real HTTP fetch, and it should also choose the gateway.
- The end-to-end order flow with `FakeGateway` and a fixed margin then runs on a laptop with no network.

Write that test first, before the change. `place_order(cid, items, FakeGateway(), ...)` with the network blocked should return a deterministic total. Today it either hangs about 2 seconds per line or returns an unmargined price.

**Next, in order:**
1. Break the status/tracking/email cycle. Have `mark_delivered` return an event, or take the sender as a parameter, so `shipping` no longer imports `notifications`.
2. Put `ON_HAND`, `LOG` and `PRODUCTS` behind small store objects that are passed in. That is what will reduce the number of files each change touches.

I haven't changed any files. Say if you want me to do step 1.