# Architecture Audit — fixture/

**Messy in places.** The move that pays most: take the rate fetch out of `pricing/quote.py`
and inject it, so the order flow runs offline.

1. **A three-module import cycle.** `orders/status.py:1` imports `shipping/tracking.py`,
   `shipping/tracking.py:1` imports `notifications/email.py`, and `notifications/email.py:1`
   imports `orders/status.py`. It loads only because each module uses the others inside
   functions. Changing what an order status means edits three packages.
2. **Network I/O inside the price calculation.** `pricing/quote.py:12` calls `urlopen`
   from `_fetch_margin`, which `unit_price` (line 18) runs once per order line. Nothing can be
   priced without the network, so `place_order` cannot run or be tested offline, and the
   `except OSError` at line 15 silently prices at 1.0 when it is down.
3. **`services/order_service.py:4` is a pass-through.** `place` only forwards to
   `orders.place.place_order`; it has one caller, `api/routes.py:2`. Delete it in your head and
   nothing is lost, so inline it.

Not findings: `core/util.py` is imported by 16 modules and imports nothing, a stable leaf,
so its fan-in is fine. `payments/gateway.py` is a real seam: the `PaymentGateway` protocol has
two adapters (`payments/live.py`, `payments/fake.py`), and it stays.

## Moves

Context: the order model and the payment flow stay as they are.

### 1. Inject the margin rate into pricing
cost:     the order flow needs the network; one HTTP call per line
files:    pricing/quote.py:10, orders/lines.py:2
owner:    `orders/lines.py` receives `margin` from its caller; `pricing/quote.py` keeps arithmetic only
callers:  orders/lines.py:5, orders/place.py:8
door:     two-way — internal signature change
proof:    place an order with a fixed margin and FakeGateway; same total as before, zero network calls
effort:   S
after:    nothing

### 2. Break the status/tracking/email cycle
cost:     three packages change together; the loop hides the dependency
files:    orders/status.py:1, shipping/tracking.py:1, notifications/email.py:1
owner:    `orders/status.py` no longer imports `shipping`; the caller passes the ETA text in
callers:  orders/status.py:8, notifications/email.py:14
door:     two-way
proof:    tests green, and `orders/status.py` imports nothing from shipping or notifications
effort:   S
after:    nothing
