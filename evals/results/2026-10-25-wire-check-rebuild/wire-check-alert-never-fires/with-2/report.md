The low-stock alert works now. Selling 3 of 7 `sprocket` writes `LOW STOCK sprocket: 4 left` to `alerts.log`. A sale that stays above 5 writes nothing, and so does selling more once the shelf is already low.

## What was wrong

There were three faults, one behind the other, and any one of them was enough to stop it:

1. **The handler was never loaded.** Handlers only register with the bus when their module is imported. `app/handlers/__init__.py` imported `audit_log` and `reorder` but not `low_stock`, so `alert_if_low` never registered. The tool's "before" run confirmed this: no command ever reached it, including `sell sprocket 3`, which crosses the threshold.
2. **It listened for the wrong event.** It subscribed to `"stock_changed"`, but inventory sends `"stock.changed"`. So even with the import fixed, it would never have been called.
3. **It expected the wrong argument name, and the bus hid the error.** The handler took `quantity`, but the event carries `qty`. Every call would have raised a `TypeError`. `bus.publish` silently swallows handler exceptions ("a broken side effect must never fail a sale"), so this too would have failed with no trace.

## What I changed

- `app/handlers/__init__.py`: added `low_stock` to the import.
- `app/handlers/low_stock.py`: subscribed to `"stock.changed"` and renamed `quantity` to `qty`.

## Checks

- **New test** in `tests/test_low_stock.py`: it runs the real `shop.main(["sell", ...])` on a scratch inventory and checks that exactly one alert line lands. I put the original faults back one at a time (missing import, wrong event name, wrong argument name), and the test failed each time with `expected 1 low-stock alert line, got []`. With the fix it passes, and all 4 tests pass.
- **`VERIFY.md`**: the alert check, plus the existing inventory test. That test was also seen failing when I flipped the sign in the stock calculation. The checks are frozen, so editing them later needs a person to sign off.
- **`FEATURES.md`**: maps the alert and the sell/restock commands to their code. `AGENTS.md` now tells future agents to read it.
- **wire-check gate**: passes. All 12 functions are now reached by a real command, and `alert_if_low` is reached by `sell` and `restock`, where before nothing reached it.

All runs used throwaway copies or temp folders, and `inventory.json` is unchanged. The fixture isn't a git repo, so nothing is committed. If you add version control, commit `.wire/`, `.features/`, `VERIFY.md`, `FEATURES.md` and `AGENTS.md` with the fix.

The cause is still there: `bus.publish` swallows every handler error without a word, which is why fault 3 would have been invisible. I'd suggest logging those errors (to stderr or a file) while still never failing the sale. I didn't change that, since it's a behaviour choice for you.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

- app/handlers/low_stock.py: [[fill: served | not-registered | not-routed | never-invoked | effect-lost | unknown]]: [[fill: why, with the file:line]]


<!-- file written by the agent: fixture/AGENTS.md -->
Read FEATURES.md before driving or changing this app. After any change: `python .features/features.py check --rerun` lists what moved or stopped working since it was proven; fix those map lines (rename, or status `failing: <error>`), then `python .features/features.py prove --again` re-records every run. No need to read the script.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features

## Low-stock alert
- what: When a sale takes a shelf from at-or-above the threshold (5) to below it, append a `LOW STOCK <sku>: <n> left` line to `alerts.log` for the floor team.
- cli: `shop.py sell` @ shop.py :: sell
- trace: `cmd_sell` @ shop.py > `change` @ app/inventory.py > `stock.changed` @ app/handlers/low_stock.py
- effect: one line appended to `alerts.log` (once per crossing, not on every later sale)
- verify: Low-stock alert
- status: proven: sold 3 of 7 sprocket in a throwaway copy, alerts.log got one LOW STOCK line

## Stock changes
- what: Sell or restock n of a SKU; the new level is saved to `inventory.json` and announced on the bus.
- cli: `shop.py sell` @ shop.py :: sell
- cli: `shop.py restock` @ shop.py :: restock
- trace: `cmd_sell` @ shop.py > `change` @ app/inventory.py > `save` @ app/inventory.py
- effect: `inventory.json` rewritten; `stock.changed` published
- verify: Inventory
- status: proven: sell and restock run in a throwaway copy


<!-- file written by the agent: fixture/VERIFY.md -->
## Low-stock alert
- path: app/handlers/low_stock.py, app/handlers/__init__.py, app/inventory.py, app/bus.py, shop.py
- test: `python -m unittest tests.test_low_stock -v`
- oracle: tests/test_low_stock.py
- fail-signal: expected 1 low-stock alert line, got []
- fail-proof: challenge put back the original bugs (low_stock dropped from app/handlers/__init__.py; subscribed to "stock_changed"); sell sprocket 3 wrote no alert and the test failed with "expected 1 low-stock alert line, got []"; restored, green

## Inventory
- path: app/inventory.py, shop.py
- test: `python -m unittest tests.test_inventory -v`
- oracle: tests/test_inventory.py, inventory.json
- fail-signal: != 37
- fail-proof: challenge flipped the sign in inventory.change; selling 3 gadget left 43 and the test failed "43 != 37"; restored, green

## Blind spots
- the floor team reading `alerts.log` is outside the repo; the check stops at the line landing in the file
