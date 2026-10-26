I ran the audit over all 53 files in `fixture/` (431 lines). I read every file and ran probes in a throwaway copy. Nothing in the repo was changed, and the skill's checker passed all three stages (`ARCH-GATE: done`). The repo has no architecture doc or ADRs to check against.

**Verdict: messy in places.** Your two complaints have separate causes. Pricing makes a network call in the middle of every order, which is why it won't run on a train. A few modules are knotted together, which is why changes spread.

## Where the structure is going wrong

1. **Pricing calls the network once per order line, and offline it quietly uses a different price** (I ran it). `pricing/quote.py:19` calls `_fetch_margin()` for each line, which hits `https://rates.example.internal` with a 2 s timeout (`pricing/quote.py:10-15`).
   - **Measured:** a 5-line order took **10.0 s** against an endpoint that accepts connections but never answers, like train Wi‑Fi.
   - **Wrong price:** any failure falls back to margin `1.0` with no log. So prices offline differ from prices online and nothing tells you. You can't trust an order flow you run on a laptop.
2. **Import cycle: `orders.status` → `shipping.tracking` → `notifications.email` → `orders.status`** (I ran it). It only works because all three files use `import pkg.mod`. Switching `notifications/email.py:1` to `from orders.status import label` raises `ImportError: partially initialized module`. Those 3 files can't be changed independently.
3. **`core/util.py` is a grab-bag** (read, not run).
   - 16 files import from it. 6 of them import names they never call; for example, `as_cents` is imported in 6 files and used in none.
   - The line `from core.util import clamp, as_cents, slug, first` appears in five files across `catalog/` and `customers/`. Renaming or removing one helper touches up to 7 files and changes no behaviour. This is a big part of why changes spread.
4. **The web route hard-wires the live payment gateway** (`api/routes.py:1,10`). The HTTP entry point can't use `payments/fake.py`. The `PaymentGateway` interface in `payments/gateway.py:4` exists but nothing references it.
5. **`services/order_service.py:4` only passes calls through.** Any change to `place_order`'s signature touches 3 files (`orders/place.py`, `services/order_service.py`, `api/routes.py`) instead of 2.

## What to do first: fetch the margin once per order and let the caller pass it in

- **What changes:** `pricing/quote.py::unit_price`. Its only callers are `orders/lines.py:1` and `orders/lines.py:6`.
- **Steps** (each one keeps today's behaviour when no margin is passed):
  1. `unit_price(sku, code=None, margin=None)`: when `margin` is None it calls `_fetch_margin()` as it does now.
  2. `build_lines(items, code=None, margin=None)`: when `margin` is None it fetches once and passes that value to every line. This alone turns N calls into 1.
  3. `place_order` and `services.order_service.place` get a `margin=None` argument that they pass straight through, next to `gateway`.
- **Result:** `api/routes.py` passes nothing, so production still fetches live. On a laptop, `place(..., FakeGateway(), margin=1.0)` makes no network call and gives a fixed price.
- **Proof:** this command passes today in a throwaway copy and runs 27 repo files. Rerun it after each step. Run it from inside `fixture/`, the repo root the checker used:
  ```
  python -B -c "import pricing.quote as q; q._fetch_margin=lambda: 1.0; from catalog.products import add_product; from inventory.stock import receive; from services.customer_service import register; from services.order_service import place; from payments.fake import FakeGateway; [(add_product(s,'Item '+s,1000), receive(s,10)) for s in 'ABC']; c=register('<email>','1 Rd','Berlin','DE'); o=place(c['id'],[{'sku':'A','qty':1},{'sku':'B','qty':2},{'sku':'C','qty':1}],FakeGateway(),'WELCOME10'); assert o['total']==6009, o['total']; print('ok', o['total'])"
  ```
- **Easy to undo:** only default arguments are added, with no stored data and no public API change.
- **Reuses the existing pattern:** `place_order` already takes its slow outside dependency, the payment gateway, as an argument (`orders/place.py:9`). The margin follows the same shape. This avoids adding a second owner for pricing config, such as a margin cache or a dependency-injection container. That would need its own refresh rules and invalidation and more to run and secure, all for one number.
- **Not taking: a module-level cache for `_fetch_margin` with an expiry time.** If we took it, the first order in each process would still wait up to 2 s offline. After one network blip it would keep the 1.0 fallback until the cache expires, again without telling anyone. Tests would also have to reset hidden global state.

After that, the next moves in order: break the cycle (finding 2) by moving `subject_for` out of `notifications/email.py` so notifications no longer import orders. Then trim the unused `core.util` imports (finding 3), and route the gateway through `payments/gateway.py` (finding 4).

## Bugs and security holes I noticed (not structural), worst first

- **Auth bypass:** `api/auth.py:5` treats whatever comes before `:` in the token as the customer id and checks nothing else. `"cus-000001:anything"` acts as that customer.
- **Stock leak:** `orders/place.py:15-16` reserves stock line by line. If a later line is short, or the charge fails, stock already reserved for earlier lines is never released.
- **Crash on unknown token:** `api/routes.py:9` crashes with `TypeError` when the token matches no account, because `current_account` returns `None`.
- **Nightly count is always 0:** nothing ever calls `orders.history.record`, so `jobs/nightly.py:7` always reports `events: 0`.

Which do you want to explore further: the margin move above, breaking the import cycle, or fixing the auth hole first?