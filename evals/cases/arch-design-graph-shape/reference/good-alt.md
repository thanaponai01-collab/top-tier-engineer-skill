# Structure review: fixture/

Verdict: sound in most places, tangled in three. Fix first: pricing reaches out over HTTP.

- **`pricing/quote.py` does I/O in domain code.** `_fetch_margin` (line 10) opens a URL in the
  middle of computing a price, once per order line. That is the reason the order flow cannot run
  on a laptop with no connection, and the `except OSError` swallows the failure by pricing at 1.0.
  Pass the rate in (a fixed one for tests, the live one in production).
- **A loop through three modules.** `orders/status.py` -> `shipping/tracking.py` ->
  `notifications/email.py` -> back to `orders/status.py`. Nothing in the imports looks wrong file
  by file; only following the chain shows it. Cut one edge: status should take the ETA as an
  argument instead of importing tracking.
- **`services/order_service.py`** is a thin wrapper around `orders.place.place_order` with no logic
  and one caller (`api/routes.py`). Fold it into the route and delete the file.

Leave alone: `core/util.py` has 16 importers but depends on nothing, so it is stable, not tangled.
And `payments/` looks over-built but is not: two implementations (live and fake) sit behind
`PaymentGateway`, so the seam is paid for.

Move 1 (inject the rate): callers `orders/lines.py:5`; proof: run the order flow with a fixed rate
and the fake gateway and get the same total as before, with no network; two-way door; size S.
