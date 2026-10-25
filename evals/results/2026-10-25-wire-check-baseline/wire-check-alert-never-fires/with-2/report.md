The low-stock alert now works. Running the real CLI on a scratch copy, `python shop.py sell widget 8` (12 → 4) writes `LOW STOCK widget: 4 left` to `alerts.log`. Selling one more widget (4 → 3) doesn't alert again, and a sale that stays above the threshold doesn't alert at all. Before the fix, the same command left no `alerts.log` at all.

## What was wrong

There were three separate breaks in a row, and fixing only one wouldn't have been enough:

1. **The handler was never loaded.** Handlers only connect to the event bus when their module is imported. `shop.py` imports `app.handlers`, but `app/handlers/__init__.py` only imported `audit_log` and `reorder`, so `low_stock` never connected.
2. **It listened for the wrong event.** It used `@subscribe("stock_changed")`, but inventory sends `"stock.changed"` (with a dot). Even when I imported it by hand, it registered under a name nothing sends.
3. **It used the wrong argument name.** The event sends `qty=`, but the handler expected `quantity`, so calling it with the real event data raised `TypeError: missing 1 required positional argument: 'quantity'`.

**Why nobody noticed:** `bus.publish` catches and discards every exception from a handler ("a broken side effect must never fail a sale"). Even with the first two breaks fixed, the `TypeError` would have been thrown away silently. Nothing could fail loudly at any step.

| Link | Before | Evidence |
|---|---|---|
| 1. File exists and loads | ✅ | ran it |
| 2. Handler connected to the bus | ❌ not in `handlers/__init__.py` | ran it: the bus listed only `audit_log` and `reorder` |
| 3. Event name matches | ❌ `stock_changed` vs `stock.changed` | ran it |
| 4. Arguments match | ❌ `quantity` vs `qty` | ran it: `TypeError` |
| 5. Line lands in `alerts.log` | ⛔ blocked by the above, ✅ after the fix | ran the CLI |

## The fix

```python
# app/handlers/__init__.py
from . import audit_log, low_stock, reorder  # noqa: F401
```
```python
# app/handlers/low_stock.py
@subscribe("stock.changed")
def alert_if_low(sku, qty, before, **_):
    if qty < LOW_STOCK_THRESHOLD <= before:
        ...
            fh.write(f"{stamp} LOW STOCK {sku}: {qty} left\n")
```

The two existing tests pass when run directly (`PYTHONPATH=. python tests/test_inventory.py`). Running `python -m unittest` finds no tests at all, because `tests/` has no `__init__.py`.

## Recommendation

Add a test that runs `shop.py sell` through the real command (not by importing the handler) on a copy of `inventory.json` crossing the threshold, and checks that `alerts.log` gets a line. That test would have caught all three breaks. Also, the bus shouldn't silently discard handler errors: logging them to stderr would keep sales from failing while making this kind of bug visible on day one.