Entry points: the `ledger` CLI, the `ledger-admin` script from pyproject (reset/reindex are live
through admin.py), the cron runner reading schedule.json (nightly_backup, purge_exports) and the
env-driven plugin loader.

Not reached, by why:
- **weekly report** (reports/weekly.py): nothing calls it at all. Orphan: either expose it or drop it.
- **compact_outbox job**: written, but not listed in schedule.json, so the runner never runs it.
  Schedule it.
- **receipts**: checkout builds the receipt and the result is thrown away; send()/enqueue() never
  run, so customers get no receipts. That is a bug to fix, not code to delete.
- **coupons**: behind COUPONS_ENABLED = False; `checkout 1 SPRING10` just ignores the code. Ask the
  owner whether to switch it on or drop it.
- **slack_hook / sheets_sync**: can't tell from the repo. They run only where LEDGER_PLUGINS
  enables them, so check each deployment's environment first.
