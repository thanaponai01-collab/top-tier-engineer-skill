It works now. Alerts fire once when a shelf crosses below 5, and not on later sales that are already under it. I tested this on a copy of the repo so your real `inventory.json` wasn't touched. The existing tests pass.

## What was wrong

There were three bugs. Any one of them on its own would have kept `alerts.log` empty:

1. **The handler was never loaded.** Handlers only sign up for events when their module is imported, and `app/handlers/__init__.py` only imported `audit_log` and `reorder`. So `low_stock.py` never ran. I added it to that import line.
2. **It listened for the wrong event name.** It subscribed to `"stock_changed"` (underscore), but `inventory.change()` sends `"stock.changed"` (dot). Even once loaded, it would never have been called. I changed it to `"stock.changed"`.
3. **It expected the wrong field name.** The event sends the new stock level as `qty=`, but the handler expected `quantity`. Calling it would have crashed with a `TypeError`. I renamed the field to `qty`, matching the other handlers.

## Why nobody noticed

`bus.publish()` catches and discards every exception a handler raises, so that a broken side effect can't fail a sale. That's why bug 3 would have failed silently even after the first two were fixed.

The swallowing is deliberate, so I left it alone. But it will hide the next broken handler just as well. I'd suggest at least logging the error to stderr there, and adding a test that sells something below the threshold and checks `alerts.log`. Tell me if you want either.

## Testing

On the copy, sprocket went 7 → 6 → 4 → 3, was restocked to 13, then went down to 4. That produced exactly two alert lines: one at 6 → 4 and one at 13 → 4.