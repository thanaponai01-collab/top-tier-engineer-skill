**Verdict: messy in places.** Do this first: take the live rates call out of `unit_price`. It is a network fetch inside pricing, and it is why the order flow can't run on a train.

The report is at `docs/arch-design.md` (next to `fixture/`). I traced the flow by reading the code and grepping imports. I didn't run the arch-design scripts, so none of it is *proven*, and I checked the file's fields by hand instead of with its checker. `fixture/` isn't a git repo, so there is no history and no co-change data.

**What's going wrong**
1. **Network call in the pricing core (strong, traced).**
   - `pricing/quote.py:10-19` calls `urllib` once per order line, with a 2 s timeout each.
   - Offline, an N-line order waits up to 2N seconds. It then silently prices at margin 1.0, so you get a wrong price with no error.
   - The payment gateway is already passed in (`place_order(..., gateway)`, and `payments/fake.py` exists). The rates fetch is the only outside call that isn't.
2. **Import cycle (strong, traced).**
   - `orders.status` imports `shipping.tracking`, which imports `notifications.email`, which imports `orders.status`.
   - The edge that closes the loop is `subject_for`, which nothing in `fixture/` calls.
3. **One argument threaded through six files (strong for the forwarding layer).**
   - `code` passes through routes, order_service, place, lines, quote and discounts.
   - `services/order_service.py` is 5 lines and has 1 caller. It forwards its 4 arguments unchanged.
4. **Smaller findings.**
   - The customer's country lookup is duplicated in `orders/place.py:11` and `shipping/rates.py:10`.
   - `orders/history.record` has no callers, yet `jobs/nightly.py` reports events from its log. This is suspected only, and I propose no deletion.

The payment seam is fine. It has a Protocol, the live gateway and a fake, so leave it alone.

**Moves, in order** (each is small, and each can be undone by reverting it)
1. Fetch the margin once at the HTTP edge and pass it into pricing. Order flow then runs offline with `FakeGateway`.
2. Make `email.subject_for` take a label string instead of importing `orders.status`. This breaks the cycle.
3. Inline `order_service` into `api/routes.py`.
4. Give shipping the single country and weight lookup.

Before Move 2, check outside `fixture/` for callers of `subject_for`, since I only searched inside it. Each move in the file has a proof step. Move 1's proof is an offline `place_order` test, and no tests exist today.

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo; analysis true of the files as read 2026-09-30)
- question: why do changes to the order flow touch too many files, and why can't it run offline?
- yardstick: add an order input like `code` (6 files today: routes, order_service, place, lines, quote, discounts); change how an order total is priced (3 modules: pricing, orders, shipping); add an order-status notification (3 modules in a cycle: orders.status, shipping.tracking, notifications.email). All three from the user's complaint plus rehearsal; no git history or issue tracker, so nothing here is measured by change-map.
- status: open
- verdict: messy in places
- context: every move assumes module-level in-memory state (ON_HAND, PRODUCTS, BOOK) and the injected-gateway style in `place_order` stay as they are.
- not read: catalog/search.py, categories.py, images.py, customers/accounts.py, reporting/*, payments/refunds.py, pricing/discounts.py, tax.py, currency.py, notifications/sms.py, templates.py. graph-audit.py, dep-map.py and change-map.py were not run; the import graph below is from grep of every `import` line in fixture/.

## Finding 1: a live network call sits inside pricing, on the order path
- where: fixture/pricing/quote.py:10-19, reached via fixture/orders/lines.py:6 and fixture/orders/place.py:10
- cost: one HTTP call per order line (`unit_price` calls `_fetch_margin` each time), 2 s timeout each. Offline, an N-line order waits up to 2N seconds, then silently prices at margin 1.0 (quote.py:14-15). It doesn't crash, so the wrong price is quiet. Gateway is injected at place.py:9; margin is the only outside call in the flow, and it is not injected.
- badge: strong
- evidence: traced (read routes -> order_service -> place -> lines -> quote; grep shows `_fetch_margin` has 1 caller, `unit_price` has 1 caller)

## Finding 2: import cycle across three modules
- where: fixture/orders/status.py:1 -> fixture/shipping/tracking.py:1 -> fixture/notifications/email.py:1 -> fixture/orders/status.py (via `import orders.status`)
- cost: 3 modules that change together; importing any one pulls in the other two. The closing edge is `email.subject_for` (email.py:14-15), which has 0 callers in fixture/ (grep), so the cycle is carried by a function nothing uses.
- badge: strong
- evidence: traced (opened all three files; grep for `subject_for`)

## Finding 3: one argument threads through 6 files, 2 of them forwarding only
- where: fixture/api/routes.py:10, fixture/services/order_service.py:4-5, fixture/orders/place.py:9-10, fixture/orders/lines.py:5-6, fixture/pricing/quote.py:18
- cost: `code` is passed through 5 signatures before use in discounts. `services/order_service.py` is 5 lines, forwards all 4 arguments unchanged and has 1 caller (routes.py:2). Adding a similar input costs the same 5 signature edits.
- badge: strong for order_service (1 caller, pure forward); worth exploring for the rest (lines/quote threading is ordinary layering)
- evidence: traced (grep for `order_service`, `place_order`, `build_lines`)

## Finding 4: the payment seam is earned, but the edge hard-wires the live side
- where: fixture/api/routes.py:1,10 (`LiveGateway()`), fixture/payments/gateway.py (Protocol), fixture/payments/fake.py
- cost: none today. Gateway has 3 implementers-in-effect (Protocol, live, fake), and `place_order` takes it as a parameter, so an order can already run with `FakeGateway`. Keep it. Only the HTTP edge picks live, which is the correct place.
- badge: speculative (not a defect; listed so it isn't "fixed")
- evidence: traced

## Finding 5: the customer's country is looked up in two places
- where: fixture/orders/place.py:11 and fixture/shipping/rates.py:10 (same `(default_address(cid) or {}).get('country', 'US')`)
- cost: 2 copies, so a change to the default country or address model edits 2 modules. Same-reason test: both mean "where does this customer ship to", so one owner is right. `place_order` also computes shipping weight as `500 * len(lines)` (place.py:13), a magic number that belongs to shipping.
- badge: worth exploring
- evidence: traced

## Finding 6: half-built or unreachable, suspected only
- where: fixture/orders/history.py:8 (`record` has 0 callers, yet fixture/jobs/nightly.py:2 reads `LOG`); fixture/notifications/email.py:14 (`subject_for`, 0 callers)
- cost: nightly reports `events` from a log nothing writes to.
- badge: speculative
- evidence: suspected (grep only; latent-audit was not run, so no deletion is proposed)

## Decision 1: how to get the margin out of pricing
- options: A) `unit_price` and `build_lines` take a `margin` argument, and the HTTP edge fetches it once per order | B) a `MarginSource` port with a live and a fixed adapter
- forces: the codebase already injects the gateway as a plain parameter (idiom match); one fetch per order instead of per line; only 1 real implementer of a margin source today plus 1 test value, so B is a guess until a second source exists. A needs 4 signatures to carry it (quote, lines, place, routes/service), which adds to the threading in Finding 3, so land Move 3 first.
- door: two-way
- evidence: traced

## Move 1: take the network fetch out of `unit_price` (headline)
- cost: order flow needs the network and pays up to 2 s per line offline; 1 outside call in pricing/quote.py:10-15, 0 ways to run `place_order` in a test without it
- pays: run the order flow on a laptop with no network (today: 2N s wait and silent margin 1.0; after: instant, explicit margin). Changing the margin source also stays inside one module.
- files: fixture/pricing/quote.py:10-20 (remove `_fetch_margin`, `unit_price(sku, margin, code=None)`); fixture/orders/lines.py:5-6; fixture/orders/place.py:9-10; fixture/api/routes.py:10 (fetch margin once, with the existing fallback to 1.0 kept here)
- owner: the HTTP edge (a small `fetch_margin()` next to LiveGateway use in api/routes.py); pricing only computes
- callers: `unit_price`: orders/lines.py:6 only; `build_lines`: orders/place.py:10 only; `place_order`: services/order_service.py:5 only (grep)
- door: two-way, land it and go
- proof: `python -c "import socket; socket.socket.connect=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('network'))"` style block inside a test that seeds `catalog.products.add_product('a','A',1000)`, `inventory.stock.receive('a',5)`, then `place_order('c1',[{'sku':'a','qty':2}],FakeGateway(),margin=1.0)` returns status `placed` with no network. Run from fixture/ as `python -m pytest` (no tests exist today, so this replaces none). Also confirm `total` equals the old value when the old fetch returned 1.0.
- effort: S
- after: nothing

## Move 2: break the orders.status / shipping.tracking / notifications.email cycle
- cost: 3 modules in one cycle (Finding 2); closing edge has 0 callers
- pays: add an order-status notification: 3 modules changed together -> the `notifications` module stops depending on `orders`; a status change no longer pulls email
- files: fixture/notifications/email.py:1,14-15 (`subject_for` takes the already-built label string, drops `import orders.status`)
- owner: orders.status owns the label; notifications only formats and sends
- callers: `subject_for`: none in fixture/ (grep); check outside fixture/ before landing
- door: two-way, land it and go
- proof: `python -c "import notifications.email, orders.status, shipping.tracking"` succeeds, and a grep for `import orders` in fixture/notifications/ returns nothing; rerun the import listing and confirm no cycle.
- effort: S
- after: nothing

## Move 3: inline `services/order_service.py` into the route
- cost: 1 file, 5 lines, 1 caller, forwards 4 arguments unchanged (Finding 3)
- pays: add an order input like `code`: 6 files -> 5 (routes calls `orders.place.place_order` directly); Move 1 adds `margin` without a fifth forwarding edit
- files: fixture/services/order_service.py:4-5; fixture/api/routes.py:2,10
- owner: fixture/orders/place.py `place_order`
- callers: routes.py:2 (import) and routes.py:10 (call), the only references (grep)
- door: two-way, land it and go
- proof: same offline `place_order` test as Move 1, plus `python -c "import api.routes"` succeeds; no reference to `services.order_service` remains (grep). `services/customer_service.py` was not read and stays.
- effort: S
- after: Move 1 (so the margin change and the inline share one edit to routes.py)

## Move 4: give shipping one owner for country and weight
- cost: 2 copies of the country lookup, 1 magic weight (Finding 5)
- pays: change the default country or address model: 2 modules -> 1
- files: fixture/orders/place.py:11,13; fixture/shipping/rates.py:9-10
- owner: shipping/rates.py (`quote_shipping(cid, lines)`); tax country can take `default_address` directly, since tax is a separate reason to change
- callers: `quote_shipping`: orders/place.py:13 only (grep)
- door: two-way, land it and go
- proof: same offline test; the total matches a value computed before the move for a US and a non-US address.
- effort: S
- after: Move 1
