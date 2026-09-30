**Verdict:** The seams are in the wrong places. Payments is already swappable, but pricing and the route aren't. There's also an import cycle that a lazy import is hiding. I read all 8 files and haven't run anything, so everything below is *traced*.

**Where it goes wrong**

1. **Pricing does network I/O inside a calculation** (`pricing/quote.py:6-15`).
   - `unit_price` fetches the tax rate over HTTP on every call, so it makes one request per order line.
   - Offline, it silently falls back to `1.0` after a 2s timeout (`quote.py:10-11`). The order flow still runs, but with a made-up rate and slowly. I suspect this is what the train problem really is. It's worse than a crash, because a wrong total can reach `charge`.
   - Nothing lets a caller supply the rate, so it can't be avoided for tests or offline use.

2. **The API route hardcodes the live gateway** (`api/routes.py:6`).
   - `post_order` builds `LiveGateway()` itself. `PaymentGateway` and `FakeGateway` exist, but nothing selects them outside tests.
   - The route can't be run locally without the real processor.

3. **Import cycle between `orders.place` and `inventory.reserve`.**
   - `reserve.py:5` imports `order_lines` lazily, and its comment says this avoids the import error at load time. That is the cycle being hidden, not fixed.
   - `order_lines` is a one-line accessor (`place.py:12-13`) that exists only to create the dependency. `reserve` could just read `order["lines"]`.

4. **Smaller problems that make changes feel heavy**
   - `services/order_service.py` is a pass-through that adds no logic, so it's one more file to touch per change.
   - `STOCK` is a module-level global (`reserve.py:1`), so state leaks between runs and tests.
   - `place_order` reserves stock before charging (`place.py:8-9`). If the charge raises, stock stays decremented, so there's no rollback.

**Do first: make the tax rate an injected dependency.**
- Give `unit_price` or `place_order` a `rate` argument or a small `RateProvider`. Keep the HTTP version as the live implementation and add a fixed-rate one for local use.
- Fetch the rate once per order, not once per line.
- Remove the silent `1.0` fallback. Let it fail, or use an explicit default that's visible to the caller.
- Then have `api/routes.py` take its gateway and rate provider from config, so both can be swapped together.

**Done means:** a test that calls `place_order(order, FakeGateway(), fixed_rate)` with the network disabled. For example, patch `urllib.request.urlopen` to raise, and it must never be called. It should fail before the change and pass after.

**Next, in order:**
1. Break the cycle by inlining `order_lines`, then drop the lazy import.
2. Decide whether `services/` earns its place. I'd delete it.
3. Fix the reserve/charge ordering, which is a behaviour change, so treat it separately.

I haven't edited anything. Want me to do step 1 with the check first?