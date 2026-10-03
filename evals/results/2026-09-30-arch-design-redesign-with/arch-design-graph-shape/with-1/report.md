**Verdict: messy in places.** Two causes are counted. A third is worth exploring. Do Move 1 first: inject the price margin so `place_order` can run offline.

**Why you can't run the order flow on a train** (*traced*, not run offline)
- `pricing/quote.py:12` calls `urllib.request.urlopen` inside `unit_price`, once per order line, via `orders/lines.py:6`. It is the only module in the graph that imports a network library.
- Offline, each line waits up to 2s and then silently prices at margin 1.0 (`quote.py:15`). A network blip in production would also change the charged price without any error.
- The payment gateway is already injected (`place.py:9`), so it doesn't have this problem.

**Why changes touch too many files**
- **No owner for the order shape** (*traced*, worth exploring): the order and line dict keys are read in 5 files across 3 modules: `orders/lines.py`, `api/schemas.py`, `reporting/sales.py` and `reporting/exports.py`. Adding a field means editing all of them.
- **Import cycle** (*proven*, strong): `notifications.email`, `orders.status` and `shipping.tracking` import each other (`email.py:1`, `status.py:1`, `tracking.py:1`). Changing an order notification touches all three.

**Moves, in order**
1. **Inject the margin.** Pass it into `unit_price`, `build_lines` and `place_order`, the same way `gateway` is passed. The HTTP fetch moves to the API edge in `api/routes.py`. It is two-way and effort S. Check: run `place_order` with `FakeGateway` and a fixed margin, with the network off.
2. **Break the cycle.** `email.subject_for` takes the label text as an argument instead of importing `orders.status`. It is two-way and effort S. `subject_for` has no in-tree callers, so external callers are the open risk.
3. **Give the order shape one owner.** Adding an order field goes from 5 files to about 2. It is effort M and lands after Move 1.

**Not acted on**
- 11 modules have no in-tree importer, including `payments/fake.py`. This is *suspected* only, and `latent-audit` would have to prove it before anything is deleted.
- `services/order_service.py` only forwards to `orders.place`. I proposed no deletion, because without git I can't see why it exists.

**Limits**
- There is no git history, so the "shotgun change" numbers come from walking the change through the code, not from co-change data. The three changes I used as the yardstick are my assumptions from your question.
- The file's `check` reports 0 broken references and 1 stale. The stale one is unfixable here, because `at:` needs a commit and the tree isn't a repository.
- I didn't run anything offline. The Move 1 check is written down but not executed.

The full write-up is in `fixture/arch-design.md`. I put it there rather than `docs/arch-design.md` because `check` resolves file paths from the file's own folder when there's no repo.

<!-- file written by the agent: fixture/arch-design.md -->
# ARCH-DESIGN
- at: no-git (the audited tree is not a repository, so there is no commit to pin)
- question: order flow: why do changes touch too many files, and why can't it run offline?
- yardstick: add a field to an order line/order (5 files, 3 modules: orders, api, reporting); change how a price is computed (1 file, but needs a network call to run); change an order-status notification (3 modules in one cycle). Source: assumed from the question, no git log or tracker available.
- status: open
- verdict: messy in places
- context: the PaymentGateway seam, the module layout and the order dict keys stay as they are.

## Finding 1: price lookup makes an HTTP call on every line
- where: pricing/quote.py:12
- cost: 1 network call per order line (build_lines at orders/lines.py:6 calls unit_price per item); place_order cannot run without network; up to 2s timeout each offline; on failure it silently prices at margin 1.0 (quote.py:15), so a network blip also changes the charged price
- badge: strong
- evidence: traced, read place.py -> lines.py -> quote.py; dep-map lists pricing.quote as the only module importing a network library. Not run offline.

## Finding 2: import cycle orders.status / shipping.tracking / notifications.email
- where: orders/status.py:1
- cost: 3 modules change together; edges email.py:1 -> status, status.py:1 -> tracking.py, tracking.py:1 -> email
- badge: strong
- evidence: proven, dep-map.py output

## Finding 3: no owner for the order shape
- where: orders/place.py:16
- cost: order/line dict keys are read in 5 files (orders/lines.py:6, orders/lines.py:10; api/schemas.py:9; reporting/sales.py:6, reporting/sales.py:10; reporting/exports.py:10); adding a field = 5 files, 3 modules
- badge: worth exploring
- evidence: traced, grep of 'cents'/'total'/'lines' keys

## Finding 4: services.order_service only forwards
- where: services/order_service.py:4
- cost: 1 layer, 1 caller (api/routes.py:2), 5 lines
- badge: worth exploring
- evidence: traced. No git, so no recorded reason for it: stays suspected; nothing to delete on this alone.

## Finding 5: unreferenced modules
- where: jobs/nightly.py:6
- cost: 11 of 53 modules have no in-tree importer, including payments.fake (the test double of the one real seam)
- badge: speculative
- evidence: suspected, static graph only. latent-audit must prove dead before anything is deleted.

## Decision 1: how to make pricing runnable offline
- options: A inject a margin provider as an argument of unit_price/build_lines/place_order (same style as `gateway`) | B mock urllib in tests
- forces: gateway is already injected (place.py:9) so A matches the code; B leaves the silent 1.0 fallback and the production coupling
- door: two-way
- evidence: traced

## Move 1: inject the margin into pricing
- cost: place_order needs the network (quote.py:12); 1 call per line
- pays: run the order flow offline: network calls 1 per line -> 0 in a test; and the fallback at quote.py:15 becomes a caller's explicit choice
- files: pricing/quote.py:10, orders/lines.py:6, orders/place.py:9-10
- owner: pricing.quote takes a `margin` value; the HTTP fetch moves to the api edge (api/routes.py:10, next to LiveGateway())
- callers: unit_price: orders/lines.py:6; build_lines: orders/place.py:10; place_order: services/order_service.py:5; place: api/routes.py:10
- door: two-way, land it and go
- proof: run place_order with FakeGateway and a fixed margin, with the network off (e.g. `python -c` calling place_order); success = returns an order with status 'placed' and no socket opened. No old tests exist to replace.
- effort: S
- after: nothing

## Move 2: break the status/tracking/email cycle
- cost: 3-module cycle (Finding 2)
- pays: change a notification: 3 modules coupled -> 1
- files: notifications/email.py:1, notifications/email.py:14, orders/status.py:1, orders/status.py:9
- owner: orders.status keeps label(); notifications.email.subject_for takes the label text as an argument instead of importing orders.status, so email no longer imports status
- callers: subject_for: none in-tree (unused def, email.py:14), so nothing else changes in-tree; external callers unknown
- door: two-way, land it and go
- proof: `python <arch-design>/scripts/dep-map.py edges.json` (after re-running graph-audit) reports CYCLES with none listed
- effort: S
- after: nothing

## Move 3: one owner for the order shape
- cost: 5 files read the order dict keys (Finding 3)
- pays: add an order field: 5 files -> 2 (the owner plus the api schema)
- files: orders/place.py:16, orders/lines.py:6, orders/lines.py:10, reporting/sales.py:6, reporting/sales.py:10
- owner: orders.lines / a small orders module exposing line_qty, order_total; reporting and schemas read through it
- callers: reporting/sales.py:6, reporting/sales.py:10; reporting/exports.py:10; api/schemas.py:9
- door: two-way, land it and go
- proof: rehearse the yardstick change again and count files; results of `revenue`/`units` unchanged on a fixed sample order
- effort: M
- after: Move 1
