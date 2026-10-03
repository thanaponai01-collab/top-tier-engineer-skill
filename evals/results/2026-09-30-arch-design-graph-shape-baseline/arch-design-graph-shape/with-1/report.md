**Verdict: messy in places, not tangled.** Do first: make pricing pure by passing the margin in (Move 1), because that is what stops the order flow running offline.

**Why it can't run on a train (proven).** `pricing/quote.py:10` does an HTTP GET to `rates.example.internal` for every order line, inside `unit_price`. A 2-line order made 2 network calls. If the call fails it silently uses margin 1.0, so an offline order gets a different price than a live one and nothing says so. The payment gateway is already injected and `FakeGateway` works, so this call is the only thing in the way.

**Why changes touch too many files.**
- **Pass-through layer (proven):** `services/order_service.py` is a one-line wrapper with one caller, `api/routes.py:10`. Adding an order input like `code` or currency means editing 6 files across 5 modules: routes, schemas, order_service, place, lines and quote. Deleting the wrapper (Move 2) makes that 5 files across 4 modules.
- **Import cycle (traced, worth exploring):** `orders/status.py` imports `shipping/tracking.py`, which imports `notifications/email.py`, which imports `orders/status.py`. It only loads because each file uses `import pkg.mod`. Adding an order state touches all three.
- **Half-built pieces (suspected, no deletions proposed):**
  - `orders/history.record()` has no callers, so `jobs/nightly.py` always reports `events=0`.
  - `customer_service.register()` has no callers.
  - 15 files import unused names from `core/util`.
  - Callers outside `fixture/` weren't checked.

**Moves, in order:**
1. **Move 1 (effort S):** `unit_price` takes `margin` as a parameter, and the fetch happens once at the API edge in `api/routes.py`. Proof: run the order with `urlopen` patched to raise. It should make 0 calls and give the same total as margin 1.0.
2. **Move 2 (effort S):** delete the wrapper and call `orders.place.place_order` from the route. It lands after Move 1.

**Limits.**
- **Made-up changes:** there is no git history, so the "next changes" are my assumptions, not observed. The counts come from reading the code by hand, not from `change-map.py`.
- **No independent recount:** I didn't have a subagent recount the Strong findings. I ran the caller checks and the order script myself.
- **Checker exit 1:** `arch-design.py check` exits 1 only on `STALE: at: no-git`, because there is no commit to point at. It reports 0 broken references.
- **File location:** the audit is at `arch-design.md` in the working directory, not `docs/`. Without a git repo the checker treats the file's folder as the repo root, so `docs/` broke every `fixture/...` reference.

<!-- file written by the agent: arch-design.md -->
# ARCH-DESIGN
- at: no-git
- question: order flow: why does one order change touch many files, and why can't it run offline?
- yardstick: add an order input like currency (6 files, 5 modules: api/schemas, api/routes, services/order_service, orders/place, orders/lines, pricing/quote); change how shipping or tax uses the address (3 files, 3 modules: orders/place, shipping/rates, customers/addresses); add an order state with a notification (4 files, 4 modules: orders/status, shipping/tracking, notifications/email, notifications/templates). Source: the user's complaint plus a hand rehearsal. No git history exists, so no change-map numbers; the changes are assumed, not observed.
- status: open
- verdict: messy in places
- context: the Python module layout, in-memory stores and the PaymentGateway protocol stay; no stored data shape or public API changes.

## Finding 1: pricing does a hidden network call per order line
- where: fixture/pricing/quote.py:10
- cost: 2 HTTP calls for a 2-line order (counted with urlopen wrapped). Nothing in the signature of unit_price (quote.py:18), build_lines (orders/lines.py:5) or place_order (orders/place.py:9) shows it. Any failure returns margin 1.0 (quote.py:14-15), so an offline run silently prices differently from a live one.
- badge: strong
- evidence: proven, ran place_order with FakeGateway: total 4830, 2 urlopen calls. The FakeGateway seam works; this call is the only thing stopping an offline run.

## Finding 2: one pass-through layer, and `code` threaded through five files
- where: fixture/services/order_service.py:4
- cost: place() is one line and has 1 caller (api/routes.py:10). The `code` parameter appears in 5 files: routes, order_service, place, lines, quote.
- badge: strong
- evidence: proven, grep for order_service shows a single import, at api/routes.py:2.

## Finding 3: import cycle orders.status -> shipping.tracking -> notifications.email -> orders.status
- where: fixture/orders/status.py:1
- cost: 3 modules in one cycle. It only imports because each file uses `import pkg.mod` and resolves the name at call time. Adding an order state touches all three.
- badge: worth exploring
- evidence: traced, read the three import lines (status.py:1, tracking.py:1, email.py:1). `python -c "import orders.status"` succeeds, so it is latent, not broken.

## Finding 4: half-built pieces that look wired
- where: fixture/orders/history.py:8; fixture/services/customer_service.py:6
- cost: record() has 0 callers, so LOG stays empty and nightly.py:7 always reports events=0. register() has 0 callers in fixture/. jobs/nightly.py:2-3 reads the LOG and ON_HAND globals directly. 15 files import unused names from core/util.
- badge: speculative
- evidence: suspected, grep found no callers, but entry points outside fixture/ were not checked. Do not delete before latent-audit proves it.

## Decision 1: how pricing gets the margin
- options: pass margin in as a value fetched once at the API edge | keep the fetch inside pricing behind an env or config switch that defaults to offline
- forces: offline runs and tests need zero network. The fetch hides a price input inside a pure calculation. A per-line fetch also cost a request per line.
- door: two-way, internal function signatures only.
- evidence: traced, unit_price has one caller (orders/lines.py:6) and build_lines has one (orders/place.py:10).

## Move 1: make pricing pure by passing the margin in
- cost: 1 hidden HTTP call per order line, and silent price drift when it fails
- pays: run the order flow offline: network calls 2 → 0 for the 2-line case. Also any pricing change stops needing a network stub.
- files: fixture/pricing/quote.py:10-20; fixture/orders/lines.py:5-6; fixture/orders/place.py:9-10; fixture/api/routes.py:10
- owner: pricing/quote.py keeps unit_price(sku, code, margin) as a pure function. A new fetch_margin() at the API edge is the only place that touches the network.
- callers: unit_price in orders/lines.py:6; build_lines in orders/place.py:10; place_order in services/order_service.py:5 (and in api/routes.py:10 once Move 2 lands)
- door: two-way, land it and go
- proof: run the fixture order script with urllib.request.urlopen patched to raise; it must produce the same total as with margin=1.0 and make 0 calls
- effort: S
- after: nothing

## Move 2: delete services/order_service.py and call orders.place from the route
- cost: one layer for one call site; every new order parameter edits one extra file
- pays: add an order input like currency: 6 files → 5, 5 modules → 4
- files: fixture/services/order_service.py:4; fixture/api/routes.py:2, fixture/api/routes.py:10
- owner: orders/place.py:9 (place_order)
- callers: api/routes.py:10 (the only one)
- door: two-way, land it and go
- proof: grep -rn order_service fixture/ returns nothing, and the offline order script from Move 1 still gives the same total
- effort: S
- after: Move 1
