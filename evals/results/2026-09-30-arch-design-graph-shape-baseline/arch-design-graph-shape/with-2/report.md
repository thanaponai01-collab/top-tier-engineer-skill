**Verdict: messy in places, not tangled.** Do first: take the network call out of pricing. It is the reason the order flow can't run offline.

**Offline (proven):** `pricing/quote.py:12` calls `urlopen` for a margin rate inside `unit_price`. `orders/lines.py:6` calls that once per order line. I ran `place_order` with `FakeGateway` and a patched `urlopen`: a 3-line order made 3 network calls. Offline, each call waits up to its 2s timeout, then prices silently fall back to margin 1.0. Payment is already injected (`place_order(..., gateway)`), and this is the only outside call in the flow.

**Too many files per change:**
- **Hand-threaded signatures (traced):** any new input to placing an order edits 4 signatures: `api/routes.py:10`, `services/order_service.py:4`, `orders/place.py:9`, and `build_lines`. `order_service.py` is 2 lines with 1 caller and adds nothing.
- **Import cycle (proven):** `orders.status → shipping.tracking → notifications.email → orders.status`. The only thing using the upward edge is `subject_for` (`notifications/email.py:14`), which has no callers in `fixture/`.
- **Country lookup (traced, speculative):** the destination country and its `'US'` default are read in `orders/place.py:11` and `shipping/rates.py:10`. I would not merge them. Tax country and shipping country could split later, for example billing vs delivery.

**Moves, in order (all two-way, all size S):**
1. Fetch the margin once at the edge in `api/routes.py` and pass it down as a value. Proof: `place_order` runs with `urlopen` raising, and `urllib` appears only in `api/`.
2. Move `subject_for` into `orders/status.py`. Proof: the cycle walk prints nothing.
3. Inline `order_service.py`. It must land after move 1.

**Gaps:**
- **No git history:** `fixture/` isn't a repository, so the change-history measure didn't run. The yardstick is my rehearsal of likely changes, not commit data. The report doesn't have real "files per commit" numbers.
- **Checker fails:** `arch-design.py check` needs a git repo, so it reports every path as missing and `at:` as stale (exit 1). The paths are real and I read each file. Run it again after `git init` and a first commit.
- **No subagent recount:** I skipped the subagent re-derivation of the strong findings. The counts come from my own greps and runs.
- **Dead code unproven:** `orders/history.record` has no callers, so `jobs/nightly.py` always reports 0 events. That is suspected dead code, not proven, and I proposed no deletion.

The full report is at `docs/arch-design.md` in the working directory, outside `fixture/`. I changed nothing inside `fixture/`.

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: no-git (fixture/ is not a repository; no history to measure)
- question: order flow: why do changes touch too many files, and why can't it run offline?
- yardstick: add a pricing input to an order (5 modules: api, services, orders x2, pricing); add an order field (3 modules: api/schemas, orders/place, reporting); add a tax country (1 module, but shipping and orders re-derive country separately). Source: rehearsal only, requirements are assumed.
- status: open
- verdict: messy in places
- context: the module layout, the injected PaymentGateway, and the in-memory stores stay; no stored data or public API shape changes.

## Finding 1: pricing makes a hidden network call, once per order line
- where: fixture/pricing/quote.py:12
- cost: place_order with 3 lines made 3 urlopen calls (one per line via orders/lines.py:6); each has a 2s timeout, so offline it is up to 6s and prices silently fall back to margin 1.0
- badge: strong
- evidence: proven, ran place_order with FakeGateway and a patched urlopen: "network calls: 3". Payment is already injected (orders/place.py:9); this is the only outside call in the flow (grep for urllib/http/socket/environ/open: one hit).

## Finding 2: import cycle, notifications knows about orders
- where: fixture/notifications/email.py:1
- cost: 1 cycle of 3 modules: orders.status -> shipping.tracking -> notifications.email -> orders.status. The only user of the upward edge is subject_for (email.py:14), which has 0 callers in fixture/.
- badge: strong
- evidence: proven, AST import walk printed the cycle; grep found no caller of subject_for. Callers outside fixture/ not checked, so dead-code status stays suspected.

## Finding 3: order parameters are threaded through 3 signatures by hand
- where: fixture/api/routes.py:10, fixture/services/order_service.py:4, fixture/orders/place.py:9
- cost: any new input to placing an order edits 3 signatures; services/order_service.py is 2 lines with 1 caller and adds nothing
- badge: worth exploring
- evidence: traced, grep for order_service and place_order found one caller each.

## Finding 4: the destination country is looked up in two places with the same 'US' default
- where: fixture/orders/place.py:11, fixture/shipping/rates.py:10
- cost: 2 copies of the default (shipping/labels.py:6 reads the address as well, for the city). Same-reason test: tax country and shipping country could split later (billing vs delivery), so do not merge them yet.
- badge: speculative
- evidence: traced.

## Decision 1: where the margin comes from
- options: pass `margin` in as a value fetched once at the edge (api) | keep fetching inside pricing behind a cache or env switch
- forces: offline runs need zero network in the flow; one fetch per order, not per line; the simplest option is a plain argument, and pricing stays pure
- door: two-way
- evidence: traced, unit_price has 1 caller (orders/lines.py:6).

## Move 1: take the margin fetch out of pricing and pass it in as a value
- cost: 3 network calls for a 3-line order; the order flow cannot run offline without waiting on timeouts (proven above)
- pays: run the order flow on a laptop offline: 3 calls, 2s timeout each → 0 calls; a test needs no patching
- files: fixture/pricing/quote.py:7-19, fixture/orders/lines.py:5-6, fixture/orders/place.py:9-10, fixture/services/order_service.py:4-5, fixture/api/routes.py:7-10
- owner: api/routes.py owns fetching the margin (move _fetch_margin and RATES_URL there, call it once per request); pricing.quote.unit_price(sku, code=None, margin=1.0) only computes
- callers: unit_price (orders/lines.py:6), build_lines (orders/place.py:10), place_order (services/order_service.py:5), place (api/routes.py:10)
- door: two-way, land it and go
- proof: in a Python session with urllib.request.urlopen replaced by a function that raises AssertionError, place_order('c1', 3 items, FakeGateway()) returns a total and `grep -rn urllib fixture/` shows only api/routes.py
- effort: S
- after: nothing

## Move 2: cut the notifications -> orders edge
- cost: 1 import cycle of 3 modules (Finding 2)
- pays: change an order status label or add a notification: no import loop, and notifications no longer needs orders to import
- files: fixture/notifications/email.py:1, fixture/notifications/email.py:14-15, fixture/orders/status.py:8
- owner: orders/status.py owns anything that builds text from an order; move subject_for there (0 callers to update), notifications/email.py keeps only send
- callers: subject_for has none in fixture/
- door: two-way, land it and go
- proof: rerun the AST cycle walk over fixture/; it prints nothing (today it prints 3 lines)
- effort: S
- after: nothing

## Move 3: inline services/order_service.py
- cost: 2 lines, 1 caller, one extra signature to edit per order input (Finding 3)
- pays: add an order input: 4 signatures → 3 (after Move 1)
- files: fixture/services/order_service.py:1-5, fixture/api/routes.py:2
- owner: orders/place.py place_order, called directly from api/routes.py
- callers: api/routes.py:10
- door: two-way, land it and go
- proof: post_order('cus-000001:x', {'items': [...]}) returns the same dict before and after; grep -rn order_service fixture/ finds nothing
- effort: S
- after: Move 1
