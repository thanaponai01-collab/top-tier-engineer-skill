# Architecture audit of `fixture/`

**Verdict: messy in places.** The order flow can't run on a train because pricing calls a remote server for every order line, and nothing lets you turn that off. The "too many files per change" problem comes from a three-way import cycle, unused helper imports and a pass-through service layer.

The helper's gate passes (`ARCH-GATE: done`). There's no architecture doc or ADR in the repo to check against. I ran the experiments in a throwaway copy and changed nothing in `fixture/`; no `__pycache__` was left behind.

## Findings

**1. Pricing calls the network once per order line.** Proven by running it.
- `pricing/quote.py:19` calls `_fetch_margin()` (`pricing/quote.py:10`) for every line, through `orders/lines.py:6`. Each call can wait up to 2 s.
- I placed a 3-line order in a temp copy. It made 3 fetches. With the server timing out it took **6.0 s**; when the server fails fast it took 0.0 s. A 10-line order could wait up to 20 s.
- There's no way to pass a margin in, so you can't run the flow offline without patching `urllib`.
- When the server can't be reached, the margin quietly falls back to 1.0. Lines in the same order can also end up priced with different margins.

**2. Import cycle: email → order status → tracking → email.** Found by reading the code.
- The chain is `notifications/email.py:1` → `orders/status.py:1` → `shipping/tracking.py:1`, and `shipping/tracking.py:11` calls back into email.
- That's 3 files in 3 packages that have to change together.
- It only loads because all three use `import pkg.mod`. Switching any of them to `from x import y` breaks it.

**3. `core.util` is imported wholesale where nothing uses it.**
- 5 files import `clamp, as_cents, slug, first` all at once: `catalog/*` (4 files) and `customers/accounts.py:2`.
- `as_cents` is imported in 6 files and called in none. Renaming it means touching 7 files with no change in behaviour.

**4. `services/order_service.py:4` only passes calls through to `orders.place`.**
- Adding one parameter to the order flow already touches 5 files: routes, order_service, place, lines and quote.

## Recommended first move: fetch the margin once per order, and let the caller supply it

`place_order` already receives the payment gateway as an argument and runs with `FakeGateway`. This move gives pricing the same treatment.

- **Changes:** `pricing/quote.py::unit_price`.
  - **Callers:** `orders/lines.py:1` and `orders/lines.py:6`.
  - **Steps:**
    1. `unit_price(sku, code=None, margin=None)` fetches only when `margin` is `None`. Rename `_fetch_margin` to `fetch_margin` and keep the old name as an alias.
    2. `build_lines(..., margin=None)` passes the margin through.
    3. `place_order(..., margin_source=fetch_margin)` calls the source once per order.
    4. Live callers use the default, so production behaviour is unchanged. Laptops and tests pass `margin_source=lambda: 1.0` alongside `FakeGateway()`.
- **Proof command** (run from the repo root before and after each step). It passes today in a copy and exercises 10 repo files:
  ```
  python -B -c "import sys; sys.path.insert(0,'.'); from catalog.products import add_product; from orders.lines import build_lines, lines_total; add_product('a','a',1000); add_product('b','b',2000); l=build_lines([{'sku':'a','qty':2},{'sku':'b','qty':1}],'WELCOME10'); assert [x['cents'] for x in l]==[900,1800], l; assert lines_total(l)==3600; print('ok')"
  ```
- **Easy to undo:** it only changes internal signatures, and the defaults keep every caller working. Reverting means 4 files.
- **Reuses** the existing way the gateway is passed in (`orders/place.py:9`, `payments/gateway.py:4`, `payments/fake.py:1`).
- **Doesn't add** an OFFLINE environment flag or a second pricing client. That would be a second live/fake switch next to the gateway argument: one more setting for every test, laptop and deploy to get right, and a code path in production that tests never run.
- **Not doing:** caching the margin in a module-level variable with an expiry time. The first order in each process would still block for up to 2 s, it still needs the network, and every test would have to reset it.

## Bugs and security issues I noticed along the way, worst first

1. **Auth trusts the token blindly.** `api/auth.py:5` takes the customer id from the text before `:` in the token and checks nothing. Anyone can place orders as any customer.
2. **Reserved stock is never released on failure.** `orders/place.py:14-16` reserves stock and then charges the card. If the charge fails, or a later line is short of stock, the earlier reservations are never released.
3. **Pricing falls back silently.** `pricing/quote.py:15` drops the margin to 1.0 when the rates server is unreachable, with no log or alert. In production that means selling at base price without anyone knowing.
4. **Nothing survives a restart.** All state (orders, stock, accounts) lives in in-memory variables, and `jobs/nightly.py` reads two of them (`orders.history.LOG` and `inventory.stock.ON_HAND`) directly.

Which should we explore: the margin move above, breaking the email/tracking cycle, or the cleanup of unused imports and the pass-through service layer?