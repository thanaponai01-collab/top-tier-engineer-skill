**Verdict: messy in places.** The order flow works and is mostly layered sensibly. The problem is that its outside dependencies are reached from deep inside the code instead of being passed in. That's why nobody can run it on a train, and some coupling makes changes spread across more files than they need to. I changed nothing in the repo. The probes ran in a throwaway copy and the helper's gate passes. The repo has no architecture doc or ADRs to check against.

## Where the structure goes wrong

1. **Pricing calls a remote rates server once for every order line** (`pricing/quote.py:7`, `:10`, `:19`, called from `orders/lines.py:6`). I placed a 3-line order through `post_order` and it made 3 network calls.
   - Each call can wait up to 2 s, so a 10-line order on a slow train connection can hang for about 20 s.
   - When the network is down it quietly uses a margin of 1.0 and gives no sign that the prices are wrong.
   - The only way to run it without the network is to monkeypatch a private function.

2. **The HTTP route always uses the live payment gateway** (`api/routes.py:1`, `:10`). A `PaymentGateway` Protocol (`payments/gateway.py:4`) and a `FakeGateway` (`payments/fake.py:1`) already exist, but the only entry point to the order flow ignores them. Running it locally means editing a file that ships to production.

3. **There is a three-file import cycle:** orders → shipping → notifications → orders (`orders/status.py:1`, then `shipping/tracking.py:1`, then `notifications/email.py:1`, used at `:15`).
   - It only imports today because all three use `import x` and look attributes up later.
   - Changing any one of them to `from x import y` breaks imports.
   - Changing how an order status is labelled pulls in shipping and email.

4. **Imports copied from file to file, plus a pass-through layer.**
   - Five files import `clamp, as_cents, slug, first` from `core.util` and use 0–2 of them (`catalog/*` ×4, `customers/accounts.py:2`). Renaming any of those helpers touches 5+ files.
   - `services/order_service.py:4` just forwards the call. Any change to `place_order`'s parameters has to edit 3 files: `place.py`, `order_service.py` and `routes.py`.

## What to do first: fetch the margin once per order and pass it in

This uses the same approach `place_order` already uses for `gateway` (`orders/place.py:9`), so it adds no new pattern:

1. Add `margin=None` to `pricing/quote.py::unit_price`. When it's `None`, it fetches the margin as it does today.
2. Add `margin=None` to `orders/lines.py::build_lines` and pass it through to `unit_price`.
3. Make `place_order` fetch the margin **once** through `pricing.quote._fetch_margin()` and pass it down. Prices stay the same, with 1 network call per order instead of one per line.
4. Pass `margin` through `services/order_service.py::place`. Production keeps the default. Laptop runs and tests pass `margin=1.0` with `FakeGateway`, so they never touch the network.

Every step keeps existing calls working because the new parameter defaults to today's behaviour. This is easy to undo.

- **Code that has to change:** `orders/lines.py:1`, `:6`, `orders/place.py:1`, `:10`, `services/order_service.py:5`, `api/routes.py:10`.
- **Proof** (run from `fixture/`): it passes today in the throwaway copy and runs 26 of the repo's files. Rerun it after each step.
  ```
  python -B -c "import sys;sys.path.insert(0,'.');import pricing.quote as q;q._fetch_margin=lambda:1.0;from catalog.products import add_product;from inventory.stock import receive;from services.customer_service import register;from payments.fake import FakeGateway;import orders.place as p;[(add_product(s,s,1000),receive(s,10)) for s in 'abc'];a=register('x@y','l','c','US');g=FakeGateway();o=p.place_order(a['id'],[{'sku':s,'qty':1} for s in 'abc'],g,'WELCOME10');assert o['total']==3464 and g.log==[('charge',a['id'],3464)],(o['total'],g.log);print('ok')"
  ```
- **Not adding:** a separate pricing-service client or margin cache. That would be a second piece of code talking to the rates server, with its own URL and timeout settings, rules for when to refresh, and its own fakes.
- **Not doing:** caching the margin in a module-level variable with an expiry time. It would still block for up to 2 s on the first order offline, hide out-of-date margins across processes, and let state leak between tests. If my move turns out to be wrong, it costs reverting four optional parameters.

## Bugs and security problems I noticed along the way (worst first)

- **Anyone can order as any customer.** `api/auth.py:5` takes the customer ID straight from the token's prefix and never checks a secret, so a token like `cus-000001:anything` works.
- **Unknown tokens crash the route:** `current_account` returns `None` and `api/routes.py:10` then fails on `acct['id']`.
- **Stock leaks on failure.** `orders/place.py:14-16` reserves stock one line at a time and never releases it. If a later line is out of stock, or the charge fails, the earlier reservations are lost.
- **IDs can repeat.** `core/ids.py` keeps its counters in memory, so order and customer IDs start again from 1 after a restart.

Which should I explore further: the margin move above, the route that hard-codes the live gateway (#2), or breaking the import cycle (#3)?