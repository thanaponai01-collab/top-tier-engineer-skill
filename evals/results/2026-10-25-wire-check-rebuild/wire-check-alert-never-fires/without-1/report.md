The low-stock alert works now. A sale that takes a shelf below 5 writes one line to `alerts.log`. Sales that leave it at 5 or above don't, and sales on a shelf that's already low don't write it again.

## What was wrong

There were three bugs, and any one of them was enough to stop the alert:

1. **The handler was never loaded.** Handlers only register with the event bus when their module is imported. `app/handlers/__init__.py` imported `audit_log` and `reorder` but not `low_stock`, so the alert never registered.
2. **It listened for the wrong event name.** The handler subscribed to `"stock_changed"` (underscore), but `inventory.change()` sends `"stock.changed"` (dot). Even if it had been loaded, it would never have been called.
3. **It used the wrong argument name.** The event sends `qty=...`, but the handler asked for `quantity`. Once it was called, Python would raise an error because `quantity` was missing.

The reason nobody noticed is in `app/bus.py`: `publish()` catches every error from a handler and silently ignores it (`except Exception: pass`), so a sale never fails because of a side effect. That meant bug 3 would have looked exactly the same as bugs 1 and 2: no output, no error, nothing in `alerts.log`.

## Changes

- `app/handlers/__init__.py`: added `low_stock` to the imports.
- `app/handlers/low_stock.py`: subscribed to `"stock.changed"` and renamed `quantity` to `qty`.
- `tests/test_inventory.py`: added a test that sells sprockets from 7 → 5 → 4 → 3 and checks that exactly one alert is written, at 4. If any of the three bugs comes back, this test fails instead of the alert just going quiet.

## Checks

- I ran the CLI on a scratch copy so the real `inventory.json` wasn't touched. Selling sprockets 7 → 6 → 5 → 4 wrote `LOW STOCK sprocket: 4 left`. Restocking to 14 and then selling down to 8 wrote nothing, which is correct.
- All 3 tests pass with `python -m unittest tests/test_inventory.py`. `python -m unittest discover -s tests` doesn't work here because `tests/` has no `__init__.py`.

## Decision for you

I left the error-swallowing in `bus.py` alone, since not failing a sale is clearly on purpose. The cost is that any future handler with a typo will fail just as silently. Printing the error to stderr instead would keep sales working and make these failures visible. That's a one-line change if you want it.