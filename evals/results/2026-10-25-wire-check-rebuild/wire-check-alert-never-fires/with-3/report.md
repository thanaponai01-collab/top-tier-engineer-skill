The low-stock alert works now. Selling 8 widgets (12 → 4) writes `… LOW STOCK widget: 4 left` to `alerts.log`. The wire-check gate finishes with `WIRE-GATE: done`: all 12 functions are entered, and the "before" snapshot confirms `alert_if_low` was never called by any command until the fix.

## What was wrong

The handler was cut off from the system in three separate places. Fixing any one or two of them would still have produced nothing:

1. **It was never loaded.** Handlers sign up to receive events when their module is imported, and `app/handlers/__init__.py` imported only `audit_log` and `reorder`. `low_stock` was never imported, so it never signed up.
2. **It listened for the wrong event.** It was subscribed to `"stock_changed"`, but `app/inventory.py` sends `"stock.changed"`. Even once loaded, it would never have been called.
3. **Its argument name was wrong.** The handler expected `quantity`, but the event sends `qty`. Every call would have failed with a `TypeError`. The bus in `app/bus.py:17` silently ignores handler errors, so this third bug would also have produced nothing, with no visible error.

The fix: add `low_stock` to the import line, change the event name to `stock.changed`, and rename `quantity` to `qty` in `app/handlers/low_stock.py`.

## Keeping it connected
- **New test, `tests/test_low_stock.py`:** runs the real `sell` command in a temp folder. It checks that dropping under the threshold writes exactly one alert line, and that a sale which stays above it writes none. I put each of the three original bugs back one at a time and the test failed every time (`expected 1 low stock alert line, got []`). It passes on the fixed code.
- **`VERIFY.md`:** records that check and the existing `tests/test_inventory.py`. Both have been seen failing on deliberately broken code, and both are locked so a later edit to them gets flagged.
- **`FEATURES.md`:** maps the `stock`, `sell` and `restock` commands and the path from a sale to `alerts.log`. Each command was run in a throwaway copy, so your `inventory.json` wasn't touched. **`AGENTS.md`** points future agents to this map.

## Worth knowing
- Because the bus swallows handler errors, any handler that breaks in future will fail just as silently as this one did. Only the tests will notice. I've listed this as a blind spot in `VERIFY.md`, and I'd consider at least logging those errors.
- An alert fires only on the sale that takes a shelf from 5 or more to under 5. Further sales below 5 don't repeat it, which I took to be what you wanted.
- This folder isn't a git repository, so nothing is committed. The new `.wire/`, `.features/`, `FEATURES.md`, `VERIFY.md`, `AGENTS.md` and the test file should be committed along with the fix.

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

## Stock changes
- what: Show stock levels, sell or restock a shelf; the count in inventory.json changes and goes out on the event bus.
- cli: `stock` @ shop.py
- cli: `sell` @ shop.py
- cli: `restock` @ shop.py
- trace: `cmd_sell` @ shop.py > `change` @ app/inventory.py > `save` @ app/inventory.py
- effect: inventory.json rewritten; `stock.changed` published
- verify: Stock changes
- status: proven: ran the CLI in a throwaway copy (receipts in .features/)

## Low-stock alert
- what: When a sale takes a shelf from 5 or more to under 5, a LOW STOCK line is appended to alerts.log for the floor team.
- cli: `sell` @ shop.py
- trace: `cmd_sell` @ shop.py > `change` @ app/inventory.py > `stock.changed` @ app/handlers/low_stock.py > `ALERTS_LOG` @ app/handlers/low_stock.py
- effect: a line in alerts.log
- verify: Low-stock alert
- status: proven: ran the CLI in a throwaway copy (receipts in .features/)


<!-- file written by the agent: fixture/VERIFY.md -->
## Low-stock alert
- path: shop.py, app/inventory.py, app/bus.py, app/handlers/__init__.py, app/handlers/low_stock.py
- test: `python -m unittest tests.test_low_stock -v`
- fail-signal: expected 1 low stock alert line
- fail-proof: challenge dropped low_stock from app/handlers/__init__.py, renamed the event to stock_changed, and renamed qty to quantity; each run went red with 'expected 1 low stock alert line, got []'

## Stock changes
- path: shop.py, app/inventory.py
- test: `python -m unittest tests.test_inventory -v`
- fail-signal: SystemExit not raised
- fail-proof: challenge loosened the negative-stock guard in app/inventory.py; test went red with SystemExit not raised

## Blind spots
- the bus swallows every handler exception (app/bus.py:17), so a handler that crashes is silent at runtime; only these checks notice
- alerts.log is only written to; nothing here checks the floor team actually reads it
