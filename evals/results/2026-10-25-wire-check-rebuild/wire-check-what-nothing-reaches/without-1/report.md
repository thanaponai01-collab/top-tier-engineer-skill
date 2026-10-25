I read every file in the repo (about 260 lines). This is based on reading the code, not running it, and I didn't change anything.

## What the codebase serves

There are three real entry points:

1. **`ledger`** (`cli:main`): `add`, `list`, `checkout`, `export`. These use `store/db.py` (orders kept in a JSON file under `LEDGER_DATA`) and `settings.py`.
2. **`ledger-admin`** (`admin:main`): `reset --yes` and `reindex`.
3. **The host's cron runs `python -m jobs.runner`**, which runs whatever is listed in `jobs/schedule.json`: `nightly_backup` and `purge_exports`.

There's also a fourth path that switches on per deployment: `cli.load_plugins()` imports `integrations.<name>` for each name in `LEDGER_PLUGINS`. The repo can't tell you whether it's ever on. That depends on the deployment environment.

## Built but not reached

| Piece | Why nothing reaches it | What I'd do |
|---|---|---|
| **`notify/receipt.py` → `send()`** and **`store/outbox.py`** | `checkout.py:15` calls `receipt.build(order)` and throws the result away. `send()` is never called, so `outbox.enqueue` never runs and nothing is written to `outbox.jsonl`. The docstring says an external mailer daemon sends from that file. | **This looks like a bug, not dead code.** Customers probably aren't getting receipts. Ask whoever runs the mailer daemon. If receipts are supposed to go out, the fix is to call `send` instead of `build`, and `notify` + `outbox` move together into a notifications service. Don't drop them. |
| **`jobs/compact_outbox.py`** | It isn't listed in `schedule.json`, and the outbox it cleans is never written to anyway. | Its fate depends on the receipt decision. If receipts get fixed, schedule it, or better, let the mailer service own its own queue cleanup. If not, delete it along with the outbox. |
| **`pricing/coupons.py`** | Only reachable when `settings.COUPONS_ENABLED` is true, and that's hardcoded `False` ("pricing review pending, see #212"). | This is switched off on purpose, not abandoned. Check where #212 stands. If the review is still live, carry coupons over and keep them off until it ends. If it was dropped, delete them. Either way, put the flag in env config the way `LEDGER_PLUGINS` is, not hardcoded. |
| **`reports/weekly.py`** | Nothing imports it, and it has no script or CLI command. Its docstring mentions "the Monday meeting", so someone may run it by hand. | Ask whoever prepares the Monday numbers. If it's used, make it a real command (`ledger report weekly`) in the service that owns orders. If not, delete it. As written, it counts *all* paid orders ever, not one week's, so even its current output is suspect. |
| **`integrations/sheets_sync.py`, `integrations/slack_hook.py`** | Only reached if a deployment sets `LEDGER_PLUGINS`. Both are also just stubs that `print` and never call Sheets or Slack. | Check the deployment environments for `LEDGER_PLUGINS`. If no deployment sets it, delete both, plus `load_plugins` and the `settings.PLUGINS` setting. If one does, the thing they're "serving" is a print line, so rebuild them properly (e.g. a consumer of order-paid events) instead of copying them over. |

## Reached, but worth a look before the split

- **`jobs/purge_exports.py`** deletes `export-*.csv` from cron's *current working directory*. `ledger export` writes wherever the user tells it to, not into a fixed export directory. So this job probably deletes nothing, or it deletes files in whatever directory cron happens to start in. Give exports a fixed location, or retire the job.
- **`admin_tools/reindex.py`** renumbers order IDs. Today that's harmless. Once receipts, Slack posts or a separate service store order IDs, it will quietly break those references. I'd drop it, or make it refuse to run once IDs are shared with anything outside the ledger.
- **`jobs/*` import `store.db._path`**, a private helper. When you split, that coupling has to become a real interface, or the jobs have to stay with the store.
- The README only covers `ledger`. `ledger-admin` and the cron runner aren't documented, so whoever operates them won't learn about them from the repo.

**Questions to settle first:** should checkout queue receipts (what does the mailer team say), does any deployment set `LEDGER_PLUGINS`, where does #212 stand, and does anyone run the weekly report.