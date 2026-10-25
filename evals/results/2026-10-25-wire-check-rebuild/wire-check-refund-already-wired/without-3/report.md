The refund command is connected and working, so I didn't change anything. Your teammate looked in the wrong place: `billing.py` never names any command, including `charge` and `balance`.

**How it's wired:**
- `billing.py` only calls `registry.all_commands()` and runs whichever command matches `argv[0]`.
- `billing_cli/registry.py:15-19` uses `pkgutil.iter_modules` to import every module in `billing_cli/commands/` the first time it's called.
- `billing_cli/commands/refund.py:5` registers itself with `@command("refund")` when that import happens. Any file dropped into `commands/` is picked up the same way.

**How I know it works:** I ran the CLI against a throwaway copy of the fixture, so your real `balances.json` wasn't touched:
- `python billing.py` with no arguments prints `usage: billing.py balance | charge | refund`, so refund was discovered.
- `refund globex 200` printed `refunded globex 200; balance 1000`, exited with 0, and the saved file showed globex at 1000.
- `refund globex 99999` printed `cannot refund 99999: globex has only 1000 on account` and exited with 1.

The README already documents `refund`.

**One gap:** there's no test for refund. `tests/` only has `test_charge.py`, so nothing would catch it if refund broke later. I can add a `test_refund.py` that follows the same pattern if you want.