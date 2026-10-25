The low-stock alert works now. Selling 8 widgets (12 → 4) writes `LOW STOCK widget: 4 left` to `alerts.log`. A later sale that is already under the threshold (4 → 3) doesn't repeat the alert, and a sale that stays above it (gadget 40 → 37) writes nothing. I ran these through `python shop.py sell …` in a fresh directory.

## What was wrong

The handler never ran, because three separate links between `shop.py` and the handler were broken. Fixing any one of them alone would not have been enough:

1. **Never registered.** Handlers only subscribe to the bus when their module is imported, and `app/handlers/__init__.py` only imported `audit_log` and `reorder`. `low_stock.py` was never loaded.
2. **Wrong event name.** The handler listened for `"stock_changed"`, but `inventory.change` publishes `"stock.changed"` (dot, not underscore). Even if it had been imported, nothing would have reached it.
3. **Wrong argument name.** The bus sends `qty=`, but the handler expected `quantity`. Every call would have raised a `TypeError`.

You saw no error at all because `bus.publish` deliberately swallows every handler exception ("a broken side effect must never fail a sale"). So the third bug would have failed silently every time, on top of the first two.

| Link | Before | Evidence |
|---|---|---|
| 1 Exists | ✅ | proven (imports fine) |
| 2 Registered | ❌ missing from `app/handlers/__init__.py` | proven (subscriber table had only audit_log and reorder) |
| 3 Routed | ❌ `stock_changed` ≠ `stock.changed` | proven (after a forced import it sat under its own event name) |
| 4 Invoked | ❌ `quantity` ≠ `qty` | proven (calling it with the real payload raised `TypeError`) |
| 5 Reachable | ✅ after the fix | proven (real CLI run wrote `alerts.log`) |

## Changes

- `app/handlers/__init__.py`: `from . import audit_log, low_stock, reorder`
- `app/handlers/low_stock.py`: `@subscribe("stock.changed")`, and the parameter is renamed `quantity` → `qty`
- `README.md`: lists `alerts.log` alongside the other handler outputs
- **New** `tests/test_handlers.py`: three tests that run the real `shop.py sell` as a subprocess and check `alerts.log`: one for crossing the threshold, one for staying above it, and one for alerting only once per crossing.

All 5 tests pass (`PYTHONPATH=. python -m unittest discover -s tests`). I also undid each of the three fixes one at a time in a scratch copy, and the new tests failed every time, so they would catch any of these bugs coming back.

## Recommendation

Test handlers by firing the real command and checking the file it writes, not by calling the handler function directly. A direct call skips the import, the event name and the payload shape, which are exactly the three things that broke here. It would also help if the bus at least logged handler exceptions to stderr instead of discarding them. Then a broken side effect still can't fail a sale, but it isn't invisible either.