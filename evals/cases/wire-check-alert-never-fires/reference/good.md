Three things were wrong, one after another; each fix only exposed the next.

1. **Never registered.** `app/handlers/__init__.py` imports only `audit_log` and `reorder`, so
   `low_stock.py` was never loaded and its `@subscribe` never ran. Added it to that import.
2. **Wrong event name.** It subscribed to `"stock_changed"`; inventory publishes `"stock.changed"`.
   Renamed the subscription.
3. **Wrong payload key, failing silently.** Inventory publishes `qty=...`; the handler took
   `quantity`, so every call raised TypeError, which the bus's `except Exception: pass` swallowed.
   The handler now takes `qty`.

Proven by running it: `python shop.py sell widget 9` (12 -> 3) writes one LOW STOCK line to
alerts.log; a further sale does not repeat it; audit.log and reorder.txt still fill in.
