The low-stock alert works now. I ran it in a scratch copy and sold widget 12 → 7 → 5 → 4. That wrote exactly one line to `alerts.log`: `LOW STOCK widget: 4 left`. Your real `inventory.json` wasn't touched.

## What was wrong

There were three separate bugs, and any one of them was enough to stop the alert:

1. **The handler was never loaded.** Handlers only register with the bus when their module is imported, and that happens in `app/handlers/__init__.py`. That file imported `audit_log` and `reorder` but not `low_stock`, so the alert function never existed at runtime.
2. **Wrong event name.** The handler listened for `"stock_changed"` (underscore). The inventory module publishes `"stock.changed"` (dot), so even once loaded it would never have been called.
3. **Wrong argument name.** The event sends `qty=`, but the handler expected `quantity`. Every call would have raised a `TypeError`.

Bug 3 shows why nobody noticed. `app/bus.py` catches every exception a handler raises and ignores it without logging anything, so that a broken side effect never fails a sale. After fixing bugs 1 and 2, the alert would still have failed silently on every sale. I left that design alone, but it's worth having the bus at least print handler errors to stderr. A one-line change there would have exposed this right away.

## Changes
- `app/handlers/__init__.py`: imports `low_stock`.
- `app/handlers/low_stock.py`: listens for `"stock.changed"` and takes `qty`.
- `tests/test_inventory.py`: new test that sends sales through the real bus. It checks that the alert fires once when the shelf crosses the threshold (5 → 4) and doesn't repeat on the next sale (4 → 3). All 3 tests pass.
- `README.md`: lists `alerts.log` with the other handler outputs.

One limitation: the alert only fires when a sale *crosses* the threshold, from 5 or more down to under 5. A shelf that was already below 5 before last week won't alert until it's restocked to 5 or more and sold down again.