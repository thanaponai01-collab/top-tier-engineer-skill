The low-stock alert now works: selling sprocket from 7 down to 3 writes `LOW STOCK sprocket: 3 left` to `alerts.log`. The handler code itself was fine; three separate mistakes kept it from ever running, and fixing any one alone would still have produced nothing.

## What was wrong

1. **It was never loaded.** Handlers only connect to the event bus when their file is imported. `shop.py` imports `app/handlers/__init__.py`, and that file imported `audit_log` and `reorder` but not `low_stock`. So the alert function never existed while the app ran.
2. **It listened for the wrong event name.** The inventory code sends `"stock.changed"`, but the handler listened for `"stock_changed"`. Even once loaded, it would never have been called.
3. **It expected the wrong argument name.** The event carries `qty=`, but the handler asked for `quantity`. Calling it raised `TypeError: missing ... 'quantity'`, and the event bus silently ignores errors from handlers (`except Exception: pass` in `app/bus.py`) so a broken side effect can't fail a sale. So this failure would have been invisible too.

The silent error handling is why nobody noticed: each mistake looked exactly like the alert simply not firing.

| Link | Before | Evidence |
|---|---|---|
| 1 File exists and loads | ✅ | proven: it imports cleanly |
| 2 Loaded by the app | ❌ not in `app/handlers/__init__.py` | proven: only `audit_log` and `reorder` were listening |
| 3 Listens for the right event | ❌ `stock_changed` vs `stock.changed` | proven |
| 4 Called with the right arguments | ❌ `quantity` vs `qty`, error hidden by the bus | proven: the `TypeError` above |
| 5 Writes to `alerts.log` | ⛔ blocked by the above | proven: no `alerts.log` after a sale that crossed the threshold |

## The fix
- `app/handlers/__init__.py`: `from . import audit_log, low_stock, reorder`
- `app/handlers/low_stock.py`: listens for `@subscribe("stock.changed")` and takes `qty` instead of `quantity`.

## How I checked it
I ran the real CLI (`shop.py sell`) in throwaway copies of the repo, so your `inventory.json` is unchanged.
- **Fixed version:** selling sprocket from 7 to 3 wrote exactly one alert line. Selling gadget from 40 to 39 correctly wrote nothing. The audit log still records both sales.
- **Each fix undone on its own:** removing the import, restoring the old event name, or restoring the old argument name each stopped the alert again.

## Recommendation
I added a regression test, `test_sale_under_threshold_writes_low_stock_alert` in `tests/test_inventory.py`. It loads the handlers the same way `shop.py` does, makes two sales, and checks for exactly one alert line. All three tests pass, and with the old event name put back the new test fails.

Two things to know about running the tests:
- **Use `PYTHONPATH=. python tests/test_inventory.py`.** `python -m unittest` finds no tests at all, because `tests/` has no `__init__.py`. That means a normal-looking test run here passes without checking anything.
- **Make handler errors visible.** Have the bus write handler exceptions to stderr (or a log) instead of discarding them. A sale still won't fail, but the next mistake like this one won't be silent.