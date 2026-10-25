The alert works now. There were three bugs, and each one alone would have kept it silent. The bus also hid all of them.

**What was wrong**

1. **The handler was never loaded.** Handlers only register with the bus when their module is imported, and `app/handlers/__init__.py` only imported `audit_log` and `reorder`. `low_stock` was never imported, so `alert_if_low` never subscribed to anything.
2. **It listened for the wrong event name.** It subscribed to `"stock_changed"` (underscore), but `inventory.change()` publishes `"stock.changed"` (dot). So even once imported, it would never have been called.
3. **It used the wrong argument name.** The event sends `sku`, `qty` and `before`, but the handler asked for `quantity`. With the first two bugs fixed, every call would have raised a `TypeError`.

Why nobody noticed: `bus.publish` catches and ignores every exception from a handler ("A broken side effect must never fail a sale"). An unknown event name is also silently a no-op. So nothing errored, nothing was logged, and the file just never appeared.

**Changes**
- `app/handlers/__init__.py`: now imports `low_stock` too.
- `app/handlers/low_stock.py`: subscribes to `"stock.changed"` and takes `qty`. The threshold logic (alert once, on the sale that takes a shelf from 5 or more to under 5) was already right and is unchanged.
- `tests/test_inventory.py`: a new test that sells sprocket 7 → 5 (no alert), 5 → 4 (one alert), then 4 → 3 (no repeat).
- `README.md`: lists `alerts.log` alongside the other handler outputs.

**Checked:** all 3 tests pass. I also ran the real CLI on a scratch copy of the shop: selling sprocket 7 → 4 → 3 wrote exactly one line, `LOW STOCK sprocket: 4 left`, and `audit.log` still recorded both sales. Your own `inventory.json` was not touched.

Two side notes, not changed:
- Run the tests with `PYTHONPATH=. python -m unittest tests/test_inventory.py`. `unittest discover` fails because `tests/` has no `__init__.py`.
- Because the bus swallows exceptions, the next broken handler will fail just as quietly. Making the bus print the error to stderr while still completing the sale would have shown this bug on day one. Happy to add that if you want it.