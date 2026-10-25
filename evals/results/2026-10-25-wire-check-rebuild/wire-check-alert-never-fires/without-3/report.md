The alert works now. There were three separate bugs, and any one of them was enough to keep it from ever writing:

1. **The handler was never loaded.** Handlers only register with the bus when their module is imported, and `app/handlers/__init__.py` imported only `audit_log` and `reorder`. So `alert_if_low` was never subscribed. I added `low_stock` to that import.
2. **It listened for the wrong event name.** It subscribed to `"stock_changed"` (underscore), but `inventory.change()` publishes `"stock.changed"` (dot). Even if it had been loaded, it would never have been called.
3. **It expected the wrong argument name.** The event sends `qty=`, but the handler asked for `quantity`. Once the first two were fixed, every call would have failed with a `TypeError`.

**Why nobody noticed:** `bus.publish()` catches every exception from a handler and silently drops it, so a sale never fails because of a broken side effect. That's reasonable, but it means a broken handler gives no sign at all. Bug 3 would have stayed hidden even after fixing the other two. I'd suggest having `publish()` at least print the error to stderr. I didn't change it because that's a behaviour change beyond this fix, but I can if you want.

**Verified:** I ran the CLI on a temporary copy so your `inventory.json` wasn't touched. Sprocket went 7 → 6 → 4 → 3, then a restock to 8, then a sale to 3. That wrote `LOW STOCK sprocket: 4 left` when it first dropped under the threshold of 5, and another alert after the restock-and-sale took it under again. It correctly wrote nothing for 4 → 3, since the shelf was already low. The existing tests pass (`python -m unittest tests/test_inventory.py`).

Changed files: `app/handlers/low_stock.py` and `app/handlers/__init__.py`.