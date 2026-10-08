**Verdict: messy in places, not tangled.** The module split is sensible and most modules are 5–20 lines. The order flow does have one live network call, one import cycle, and a few lost invariants. Outcome chosen: **Improve**, with local moves only. Nothing here justifies replacing a part. Every finding below is *traced*: I read the whole chain. Nothing was run, and there are no tests, no `git` history and no tracker in `fixture/`.

## The one move that pays most

**Take the network call out of price calculation.** `pricing/quote.py:19` calls `_fetch_margin()` (`:10-14`), which does `urllib.request.urlopen(...)` against `rates.example.internal` with a 2s timeout. It runs once per order line, because `orders/lines.py:6` calls `unit_price` for each item.

- **Why the train fails:** an order of N lines makes N network calls, each of which can wait up to 2s offline. The order flow can't run or be tested without that host.
- **It also hides a pricing bug:** `except OSError: return 1.0` (`quote.py:14`) quietly prices at margin 1.0 when the host is unreachable. A customer can be charged a different amount depending on the network, and nothing logs it.
- **Better shape (improve):** `unit_price(sku, code, margin)` becomes pure, and `place_order` receives the margin as an argument, the same way it already receives `gateway`. A failed fetch should raise an error instead of returning 1.0.
- **Second option:** keep the fetch inside `pricing`, but cache it and inject the fetcher. That costs more and still leaves a hidden dependency.
- **Door:** two-way. This is a function signature and has no stored data.
- **Steps, each landing alone:**
  1. Add a `margin` parameter, defaulting to the current fetch so behavior is unchanged.
  2. Fetch the margin once per order in `place_order`.
  3. Pass a fixed margin in tests and local runs.
  4. Decide the failure rule: raise, or fall back to 1.0 with a log line.
- **Proof:** `place_order(...)` with `FakeGateway` and no network returns a total identical to a run with the network up. Network calls per order go from N to ≤1 (or 0 locally).

## Ranked findings

**2. Import cycle: `orders.status` → `shipping.tracking` → `notifications.email` → `orders.status`.**
- The edges are at `orders/status.py:1`, `shipping/tracking.py:2` and `notifications/email.py:1`.
- It is not on the placement path, but these three modules can only change together.
- Two reasons it exists:
  - `label()` pulls the delivery ETA from `shipping`.
  - `subject_for()` pulls the label from `orders`.
- **Better shape (improve):** make `subject_for` take the label string as an argument, so `email.py` no longer imports `orders.status`. That is 1 import removed and the cycle is gone.
- **Second option:** have `orders.status` stop calling `shipping`, and pass `eta` in. This is also two-way.
- **Proof:** `python -c "import notifications.email"` has no circular import, and `shipping.tracking` can be imported alone.

**3. Placement isn't atomic, and the audit trail is missing.**
- `orders/place.py:14-15` reserves stock per line, then `:16` charges. If line 3 is short, lines 1–2 stay reserved. If the charge fails, all lines stay reserved. `inventory.reserve.release` exists, but nothing calls it.
- `orders.history.record` is never called anywhere in `fixture/`. `jobs/nightly.py` counts `LOG`, which stays empty.
- **Better shape (improve):** charge first, or reserve with a `try/except` that calls `release` on failure. Then `record(order_id, 'placed')` after success.
- **Proof:** a test with `FakeGateway` that raises, followed by an assertion on `ON_HAND` for stock restored.
- These are behavior changes, so each is its own step, separate from the structural moves.

**4. The order is a bare dict with no owner.**
- `place.py:16` builds it, and four other files read its keys: `api/schemas.py:8`, `reporting/sales.py:6-10`, `orders/status.py:11,15` and `jobs/nightly.py`.
- Adding or renaming a field means editing the builder and every reader. That is the "changes touch too many files" feeling.
- **Better shape (improve):** one `Order` dataclass (or `TypedDict`) in `orders/`, which readers import. This is a type change with the same runtime data.
- **Second option:** leave the dict and add a single contract test. That's cheaper but doesn't stop drift.
- **Proof:** "add a field to the order" goes from about 3 files to 2 (the builder plus the one reader that shows it).

**5. Duplicated country lookup.**
- `(default_address(cid) or {}).get('country', 'US')` appears at `orders/place.py:11` and `shipping/rates.py:15`.
- Both do the same job, so the same-reason test passes. Shipping should take `country` as an argument, as `tax_for` already does.
- The magic `500 * len(lines)` at `place.py:13` is a weight guess with no name. Give it one.
- **Proof:** `grep "'US')"` shows 1 hit instead of 2, and changing the default country is one edit.

**6. A forwarding layer.**
- `services/order_service.py` is 5 lines with one caller (`api/routes.py:2`). It adds nothing to `place_order`, and inlining it makes the complexity vanish.
- **Do not touch `customer_service.py`.** It really orchestrates three modules.
- Before deleting, check why it exists. There is no `git` history here, so call the deletion *suspected*.

**7. Smaller notes.**
- `api/routes.py:10` hard-codes `LiveGateway()`. The injection seam in `place_order` is right, but a laptop run needs another entry point. Moving the choice to one factory is a small change.
- Several files import `clamp, as_cents, slug, first` and use none of them (`catalog/*.py`, `customers/accounts.py`, `inventory/stock.py`). Dropping them is pure tidying, and `core/util.py` is a grab-bag.
- `pricing/currency.py`, `payments/refunds.py` and `inventory/warehouses.py` have no callers inside `fixture/`. That doesn't prove they are dead, because callers might live outside this tree. Treat them as *suspected* and leave them alone unless `latent-audit` confirms.

**What is fine and should stay:** `PaymentGateway` has two real implementers (`live.py` and `fake.py`), so it earns its place. State is in-memory dicts, which is why the flow could otherwise run offline. This is a stable foundation, not a flaw.

**Build order:** 1 → 3 → 5 → 4 → 2 → 6. Move 1 is what unblocks working offline. Move 3 fixes a real data-loss path.

Nothing was written. The offer to render this as a Mermaid or `arch-map` diagram is open if you want one.