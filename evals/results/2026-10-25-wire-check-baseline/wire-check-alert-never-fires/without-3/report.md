The low-stock alert works now. There were three bugs, and any one of them on its own would have stopped it writing anything:

1. **The handler was never loaded.** Handlers only register with the bus when their module is imported, and `app/handlers/__init__.py` imported only `audit_log` and `reorder`. So `low_stock.py` never ran. I added it to the import list.
2. **It listened for the wrong event name.** It subscribed to `"stock_changed"`, but `inventory.change()` sends `"stock.changed"` (with a dot). Even if it had been loaded, it would never have been called.
3. **It used the wrong argument name.** The event sends `qty=`, but the handler expected `quantity`. Once the first two bugs were fixed, every call would have crashed with a `TypeError`. You wouldn't have seen that crash, because `bus.publish` catches and discards every handler exception so a side effect can't break a sale. I renamed the argument to `qty`, the name the other handlers use.

**Verified:** I ran sales on a copy of the inventory so your real `inventory.json` wasn't touched. Selling sprocket from 7 down to 4 wrote `LOW STOCK sprocket: 4 left` to `alerts.log`. Widget sales that stayed at 6 or above wrote nothing, which is correct. The alert only fires on the sale that takes a shelf under 5, so it won't repeat on every sale after that.

I also added a regression test to `tests/test_inventory.py` that checks the alert is written at that point. All 3 tests pass when run with `PYTHONPATH=. python -m unittest tests/test_inventory.py`. Plain `unittest discover` fails because `tests/` has no `__init__.py`; that has nothing to do with this fix.

**Worth deciding:** because the bus throws away handler errors, any future bug in a handler will fail just as silently as bug 3 would have. I'd suggest having it log the exception to stderr (or a log file) instead, so sales still go through but broken handlers get noticed. I haven't made that change.