The low-stock alert works now. Selling widget from 12 down to 4 writes `LOW STOCK widget: 4 left` to `alerts.log`. Your real `inventory.json` was never touched: all runs happened in throwaway copies.

## What was wrong

The handler was broken in three separate places. Each one alone was enough to keep it from writing anything:

1. **It was never loaded.** Handlers only subscribe to the bus when their module is imported, and `app/handlers/__init__.py` imported only `audit_log` and `reorder`. `low_stock.py` never ran at all. The before-snapshot confirms it: `sell widget 8` went from 12 to 4, crossing the threshold, and never entered `alert_if_low`.
2. **It listened for the wrong event name.** It subscribed to `"stock_changed"`, but `inventory.change` publishes `"stock.changed"`, so even once loaded it would never have been called.
3. **It expected the wrong argument name.** The bus sends `qty=`, but the handler asked for `quantity`. That would have caused a `TypeError` on every sale, and `bus.publish` silently swallows exceptions from handlers ("a broken side effect must never fail a sale"). So fixing only 1 and 2 would still have given an empty log with no error shown anywhere.

## The fix
- `app/handlers/__init__.py`: also imports `low_stock`.
- `app/handlers/low_stock.py`: subscribes to `"stock.changed"` and uses `qty`.

## How I checked it
- **Real CLI runs:** a sale from 12 to 4 writes exactly one line. Selling 4 to 3 doesn't write a second one, because the alert fires only when a shelf crosses below 5. Restocking writes nothing.
- **New test, `tests/test_low_stock.py`:** it drives `shop.main(["sell", ...])` and reads `alerts.log`. With the event-name bug put back, it fails with `expected 1 low-stock alert line, got []`; with the fix it passes.
- **wire-check:** all 12 functions are now reached by a real command (11 before), and its gate reports done.
- **Feature map:** `.features/features.py check --strict --rerun` comes back fully clean.

## Files added
To keep this from silently breaking again, the skill had me add these:
- `VERIFY.md`, with two checks: the low-stock alert and the existing inventory test.
- `FEATURES.md` with `.features/`, a map of the features and how each is reached.
- `AGENTS.md`, which tells the next agent the map exists.
- `.wire/`, `.verify-state.json` and `.verify-state-cache/`, the helpers' recorded results.

The folder isn't a git repo, so I haven't committed anything. The skill says these files should be committed along with the fix.

One risk remains: `bus.publish` swallowing exceptions is why bug 3 would have stayed invisible. You may want it to at least log the error.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.



<!-- file written by the agent: fixture/AGENTS.md -->
Read FEATURES.md before driving or changing this app. After any change: `python .features/features.py check --rerun` lists what moved or stopped working since it was proven; fix those map lines (rename, or status `failing: <error>`), then `python .features/features.py prove --again` re-records every run. No need to read the script.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features

## Low-stock alert
- what: When a sale takes a shelf under 5, append a LOW STOCK line to alerts.log for the floor team.
- cli: `sell` @ shop.py
- trace: `cmd_sell` @ shop.py > `change` @ app/inventory.py > `stock.changed` @ app/handlers/low_stock.py > `ALERTS_LOG` @ app/config.py
- effect: one line in alerts.log per shelf crossing the threshold
- verify: Low-stock alert
- status: proven: sold widget 12 -> 4, alerts.log got one line

## Sell and stock count
- what: Take items off the shelf and keep inventory.json in step.
- cli: `stock` @ shop.py
- cli: `restock` @ shop.py
- trace: `cmd_sell` @ shop.py > `change` @ app/inventory.py > `save` @ app/inventory.py
- verify: Sell and stock count
- status: proven: ran stock, sell and restock in a throwaway copy


<!-- file written by the agent: fixture/VERIFY.md -->
## Low-stock alert
- path: app/handlers/low_stock.py, app/handlers/__init__.py, app/bus.py, app/config.py, app/inventory.py, shop.py
- test: `python -m unittest tests.test_low_stock -v`
- oracle: tests/test_low_stock.py, inventory.json
- fail-signal: expected 1 low-stock alert line, got []
- fail-proof: subscribed the handler to "stock_changed" again (the original bug), test went red with no alert line, reverted

## Sell and stock count
- path: app/inventory.py, shop.py
- test: `python -m unittest tests.test_inventory -v`
- oracle: tests/test_inventory.py, inventory.json
- fail-signal: AssertionError: 40 != 37
- fail-proof: made change() ignore the delta, sale left gadget at 40, test went red, reverted
