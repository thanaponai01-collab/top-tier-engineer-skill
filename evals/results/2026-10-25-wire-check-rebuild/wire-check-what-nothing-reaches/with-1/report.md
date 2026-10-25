I ran every way into the ledger repo in a throwaway copy and recorded which functions each run actually entered. 18 of the 23 functions are reached. The other 5 fall into four pieces, and one of them is a live bug rather than dead code.

## What the codebase serves

| Way in | What it reaches |
|---|---|
| `ledger` (`cli.py::main`) | `add`, `list`, `checkout`, `export`, through `store/db.py` |
| `ledger` with `LEDGER_PLUGINS` set for a deployment | `sheets_sync` adds a `sync-sheet` command; `slack_hook` wraps `checkout` to post to Slack. Both ran when I set the variable |
| `ledger-admin` (`admin.py::main`) | `reset` (needs `--yes`) and `reindex` |
| Host cron: `python -m jobs.runner` | Only what `jobs/schedule.json` lists: `nightly_backup` and `purge_exports` |

All of this is in use and should carry over.

## What got built that nothing reaches

**1. Customer receipts: a bug, not dead code (`notify/receipt.py::send`, `store/outbox.py`)**
`commands/checkout.py:14` calls `receipt.build(order)` and throws the result away. `send()` is the only thing that writes to the outbox, and nothing calls it. So no paid order has ever queued a receipt for the mailer daemon. The module's docstring says one receipt goes out per paid order, so this looks like a slip, not a choice.
→ **What I'd do:** settle it before the split. Ask whoever owns the mailer whether customers should be getting receipts. If yes, the fix is one word: `receipt.send(order)` at `checkout.py:14`. Receipts then belong with checkout/notifications in the new layout. If no, delete `send` and `store/outbox.py`, and tell the mailer side that its input is permanently empty.

**2. `jobs/compact_outbox.py`: never scheduled**
`schedule.json` doesn't list it, and that file is the only thing the job runner reads. Even if it were scheduled, it would compact an outbox that nothing writes to.
→ **What I'd do:** depends on item 1. If receipts get turned on, move it with the notification service and add it to the schedule, or the outbox grows forever. If receipts are dropped, delete it.

**3. `pricing/coupons.py`: switched off on purpose**
It only runs when `settings.COUPONS_ENABLED` is true (`checkout.py:9`). That flag is hard-coded `False` at `settings.py:4` with "pricing review pending, see #212". Unlike the plugins, it isn't read from an environment variable, so no deployment can turn it on. Side effect: `ledger checkout 1 SPRING10` silently charges full price.
→ **What I'd do:** don't carry it over by default. Check where #212 stands. If coupons are still planned, keep them as a clearly-flagged piece of the pricing service. Make the flag configurable, and reject unknown or disabled codes instead of ignoring them. If #212 is dead, delete the module and the coupon argument to `checkout`.

**4. `reports/weekly.py`: nothing calls it**
Nothing imports it: no CLI command, admin command, or scheduled job. Its docstring says it's for the Monday meeting, so someone may be running it by hand from a Python shell. Nothing in the repo shows that.
→ **What I'd do:** ask whoever runs the Monday meeting. If they still use it, give it a real way in (an `admin` command or a scheduled job) in whichever service owns reporting. If nobody claims it, leave it behind. It's 5 lines and easy to rebuild from `db.load()`.

## Caveats
- Every run started with an empty data directory, so `checkout` had to be chained after `add` in a single command.
- Plugins were only exercised with the environment variable I set. Whether any real deployment sets `LEDGER_PLUGINS` isn't visible from the repo. Check deployment config before assuming `sheets_sync` and `slack_hook` are in use.
- I didn't touch the code. The tool wrote a `.wire/` folder (`snapshot.json` and `verdicts.md`, holding the above with file:line citations) into `fixture/`. Keep it as a record for the split or delete it.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

- notify/receipt.py::send: effect-lost: checkout builds the receipt and drops it — commands/checkout.py:14 calls receipt.build(order) and discards the return; send(), the only path to the outbox, is never called, so no receipt ever reaches the mailer
- store/outbox.py: effect-lost: only caller is notify/receipt.py:14 (send), which is itself dropped at commands/checkout.py:14
- jobs/compact_outbox.py: not-registered: not listed in jobs/schedule.json (only nightly_backup, purge_exports), which is the only thing jobs/runner.py:11-12 runs; and the outbox it compacts is never written (see above)
- pricing/coupons.py: never-invoked: guarded by settings.COUPONS_ENABLED at commands/checkout.py:9, hard-coded False at settings.py:4 ("pricing review pending, see #212"); not an env var, so no deployment can turn it on
- reports/weekly.py: not-registered: nothing imports reports.weekly; no CLI, admin, or scheduled job names it
