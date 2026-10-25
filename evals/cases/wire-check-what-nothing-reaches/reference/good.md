## Ways in
- `ledger` (cli:main): add, list, checkout, export.
- `ledger-admin` (admin:main, second console script in pyproject.toml): reset, reindex.
- cron: `python -m jobs.runner`, which loads each job in jobs/schedule.json by name.
- plugins: cli.load_plugins imports `integrations.<name>` for each name in LEDGER_PLUGINS.

## Served
commands/*, store/db.py, admin_tools/reset.py and reindex.py (via ledger-admin),
jobs/nightly_backup.py and purge_exports.py (in schedule.json).

## Built but not reached
| piece | first broken link | what I'd do |
|---|---|---|
| reports/weekly.py | not registered: no command, job or entry names it | wire it as `ledger report`, or delete it |
| jobs/compact_outbox.py | not routed: schedule.json does not list it, so nothing runs it | add it to the schedule (the outbox grows forever) |
| notify/receipt.py send + store/outbox.py | effect lost: checkout calls `receipt.build(order)` and discards the return value; nothing ever enqueues | a live bug: call `receipt.send(order)` |
| pricing/coupons.py | never invoked: COUPONS_ENABLED is False with no override; the coupon argument is silently ignored | owner decision (#212) |
| integrations/slack_hook.py, sheets_sync.py | unknown: loaded only when LEDGER_PLUGINS names them per deployment | check the deployment config before moving or dropping |

Proven by running each entry; the plugin loads checked with LEDGER_PLUGINS=slack_hook,sheets_sync.
