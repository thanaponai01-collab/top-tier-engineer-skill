**Verdict: messy in places.** The first thing to do is Move 1: stop pricing from calling the network once per order line.

The file is `arch-design-fixture.md`, next to `fixture/`. Its checker reports 0 broken references and 1 `STALE`. The `STALE` is only because `fixture/` isn't a git repo, so `at:` can't name a commit. There was no history to measure either, so the evidence is a rehearsal of the code, not co-change counts.

**Where the structure goes wrong**
1. **Pricing calls the network once per line** (`pricing/quote.py:8,15`, `orders/place.py:7`). A 2-line order made 2 HTTP calls. Offline, the `except OSError` at `quote.py:11` returns a rate of 1.0, so the order is priced with no tax and nothing is raised or logged. This is what blocks the train scenario, and it is also a silent pricing bug. *Proven* by running it.
2. **The fake payment gateway exists but nothing uses it.** `api/routes.py:6` hardcodes `LiveGateway`, and `FakeGateway` has no references outside its own file. The seam is built but never wired. *Traced.*
3. **`orders` and `inventory` import each other.** `inventory/reserve.py:5` hides the cycle with a lazy import, and moving it to the top of the file raises an `ImportError`. Inventory only needs `order["lines"]`, so it depends on the order's shape. That is why changing an order field reaches inventory. *Proven* by running it.
4. **`services/order_service.py` only forwards one call.** It has 1 caller and 2 lines, and it adds a hop to every order-flow edit. I rated this "worth exploring", because there is no git history to say why the layer exists.

**Moves, in order (all S-sized and two-way)**
1. Fetch the tax rate once per order and pass it into `place_order`, so the flow runs with zero network calls.
2. Pick the gateway in one `make_gateway()` that reads an env var. It defaults to live, so production behaviour doesn't change.
3. Pass `{sku, qty}` lines to `reserve`, which removes the cycle.
4. Inline `order_service`. Confirm first that no second caller is planned.

**One decision needs the owner.** When the tax rate is unavailable, should the order fail or fall back to 1.0? That is a business rule I can't see from the code. Move 1 keeps the current fallback, so it doesn't decide this, but the silent no-tax path stays until someone does.

**Adjacent, not filed:** `place_order` reserves stock before it charges (`orders/place.py:8-9`). If the charge fails, nothing puts the stock back. `payments/gateway.py:6` also mentions a `PaymentError` that doesn't exist.

I skipped the independent subagent recount. The two Strong findings I proved myself rest on runs I did in this session, and the fixture is 9 small files.

<!-- file written by the agent: arch-design-fixture.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo; analysis is of the files as read 2026-09-30)
- question: order flow in fixture/: why does every change feel heavy, and why can't it run on a laptop offline?
- yardstick: add an order field, e.g. currency (touches 3 modules: api, orders, pricing); change tax/pricing rules (2 modules: pricing, orders); swap or add a payment provider (2 modules: payments, api). Source: rehearsal only, no history and no tracker; these are assumed, not requested.
- status: open
- verdict: messy in places
- context: Python, in-process, one order flow (api -> place -> price, reserve, charge). The PaymentGateway Protocol and FakeGateway stay as they are. No stored data shape or public API changes in any move.

## Finding 1: Pricing makes a network call per order line, hardwired, and fails open to "no tax"
- where: fixture/pricing/quote.py:8, fixture/pricing/quote.py:11, fixture/pricing/quote.py:15, fixture/orders/place.py:7
- cost: 1 outbound HTTP call per line (2 calls for a 2-line order, counted by a spy on urlopen). The call has no injection point, unlike payments. Offline, the `except OSError` returns 1.0 (quote.py:11), so the order is priced without tax and nothing is raised or logged. A 2 s timeout per line makes a hung network cost 2 s x lines.
- badge: strong
- evidence: proven. Ran place() with FakeGateway and counted 2 urlopen calls. Code path read end to end.

## Finding 2: The composition root hardwires the live gateway, so the existing fake can't be used
- where: fixture/api/routes.py:1, fixture/api/routes.py:6, fixture/payments/fake.py:2
- cost: FakeGateway's docstring says it is for "test suite and local dev". The only place a gateway is chosen (routes.py:6) hardcodes LiveGateway, and FakeGateway has 0 references outside its own file. The seam is built but not wired, so the HTTP entry point can only run against the live gateway.
- badge: strong
- evidence: traced. Grepped the whole fixture for FakeGateway and LiveGateway; single construction site.

## Finding 3: orders <-> inventory import cycle, hidden by a lazy import
- where: fixture/inventory/reserve.py:5, fixture/orders/place.py:1, fixture/orders/place.py:12
- cost: 1 cycle. inventory (lower) imports orders (higher) only to call `order_lines`, which returns `order["lines"]` (place.py:13). The comment at reserve.py:5 admits the cycle. Moving the import to module top fails with ImportError (circular import).
- badge: strong
- evidence: proven. Copied the fixture, moved the import to the top of reserve.py, and `import orders.place` raised the circular ImportError.

## Finding 4: services/order_service.py is a pass-through layer
- where: fixture/services/order_service.py:4, fixture/api/routes.py:2
- cost: 1 function, 2 lines, 1 caller (routes.py:6). It only renames `place_order` to `place`. Every order-flow edit has to go through an extra hop and name.
- badge: worth exploring
- evidence: traced. Grep found one caller. There is no git history, so no recorded reason for the layer exists. Treat it as suspected-unknown until someone confirms it isn't there for a planned second caller.

## Decision 1: Where the tax rate comes from
- options: A) `place_order` takes a `rate` (or a `price` callable) from its caller, and the caller fetches it once per order; the fetch stays in pricing | B) a `Pricer` protocol with live and fake implementations, mirroring PaymentGateway
- forces: the offline requirement and the per-line cost push towards injection. There is one real implementation today, so a Protocol would be a seam with 1 caller and under 100 lines (skill bar): A is the simplest thing that meets the requirement. A fake pricer would be the second implementation, which justifies B later.
- door: two-way (internal function signature, behind the api boundary)
- evidence: traced. Read pricing/quote.py and orders/place.py in full.

## Decision 2: What to do when the rate is unavailable
- options: A) raise, so an order is never priced without tax | B) keep returning 1.0, but log it
- forces: silently dropping tax is a correctness risk. Whether a failed price should reject the order or fall back is a business rule I can't see from the code. The local/offline path gets its rate from the injected value (Move 1), so it doesn't need the fallback.
- door: two-way in code, but the behavior change is visible to customers. Needs the owner's yes before Move 1 changes it. Move 1 as written keeps the current fallback, so it doesn't decide this.
- evidence: traced. quote.py:10-11 read; no other handler exists for this case.

## Move 1: Price an order with one injected rate instead of a live fetch per line
- cost: 2 urlopen calls for a 2-line order (N for N lines); no way to run the order flow without the network (Finding 1)
- pays: "run the order flow offline / in a test": network calls 2 -> 0. "Change tax rules": editing 2 modules stays 2 but pricing no longer runs inside order placement.
- files: fixture/pricing/quote.py:6-15, fixture/orders/place.py:5-7, fixture/api/routes.py:6
- owner: pricing/quote.py owns the rate fetch; orders/place.py owns the arithmetic and receives the rate
- callers: `unit_price` in place.py:7; `place_order` in order_service.py:5; `place` in routes.py:6. Nothing else (grep)
- door: two-way, land it and go
- proof: `cd fixture && python -c "import urllib.request as u; u.urlopen=lambda *a,**k:(_ for _ in ()).throw(AssertionError('network'))"` then place an order with FakeGateway and a rate of 1.0; it must return `fake-1` with zero urlopen calls. A second check: a 2-line order makes at most 1 rate fetch in live mode.
- effort: S
- after: nothing

## Move 2: Choose the gateway in one place, from config, with the fake available
- cost: 0 uses of FakeGateway outside its file; routes.py:6 constructs LiveGateway on every request
- pays: "run the order flow on a laptop": the HTTP entry point can run with no processor. "Swap or add a payment provider": api + payments -> 1 place.
- files: fixture/api/routes.py:1-6, fixture/payments/fake.py:1
- owner: a single `make_gateway()` in payments/ that reads an env var (e.g. `PAYMENTS=fake|live`, default live so production behavior is unchanged)
- callers: `post_order` (routes.py:6), the only construction site
- door: two-way, land it and go
- proof: `PAYMENTS=fake python -c "from api.routes import post_order; print(post_order({...}))"` returns a `fake-` charge id; with the variable unset it returns `live-...`
- effort: S
- after: Move 1

## Move 3: Break the orders <-> inventory cycle by passing lines to `reserve`
- cost: 1 import cycle, hidden by a lazy import (reserve.py:5)
- pays: "add an order field" or "change inventory rules": inventory stops depending on the order's shape, so an order-field change no longer reaches reserve.py. 2 modules -> 1.
- files: fixture/inventory/reserve.py:4-8, fixture/orders/place.py:8 and :12-13
- owner: orders owns the order shape and hands inventory a list of `{sku, qty}`; inventory knows nothing about orders
- callers: `reserve(order)` in place.py:8 (the only call site); `order_lines` in reserve.py:7 (the only caller, delete it with the lazy import once unused)
- door: two-way, land it and go
- proof: move the import to module top is no longer needed: `cd fixture && python -c "import inventory.reserve, orders.place"` succeeds, and `grep -rn "orders" inventory/` returns nothing
- effort: S
- after: nothing

## Move 4: Inline the order_service pass-through
- cost: 1 extra module and hop for 1 caller (order_service.py:4-5)
- pays: "change the order flow": one fewer file on the path, api -> orders directly (3 hops -> 2)
- files: fixture/services/order_service.py:4-5, fixture/api/routes.py:2
- owner: orders/place.py, called directly by routes.py
- callers: `place` in routes.py:6 (the only one)
- door: two-way, land it and go. Confirm first that no second caller (a worker, a CLI) is planned, because no history explains why the layer exists.
- proof: `grep -rn "order_service" fixture/` returns nothing after the move, and the Move 2 proof still prints `fake-` charge ids
- effort: S
- after: Move 2
