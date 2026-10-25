Short version: the CLI, the admin tool and the cron jobs are all live. **One whole subsystem, customer receipts, is built but never fires, and that looks like a bug rather than leftover code.** There's also one report nothing calls. I read every file in `fixture/` and changed nothing.

## What the codebase serves

There are three entry points: two commands declared in `pyproject.toml` and one cron job.

| Entry point | Reaches |
|---|---|
| `ledger` (`cli.py:main`) | `commands/add`, `listing`, `checkout`, `export` → `store/db`, `settings` |
| `ledger-admin` (`admin.py:main`) | `admin_tools/reset`, `admin_tools/reindex` → `store/db` |
| Host cron: `python -m jobs.runner` | whatever is listed in `jobs/schedule.json`: `nightly_backup`, `purge_exports` |

Two areas need a judgement call rather than a simple "used" or "unused":

- **`pricing/coupons.py`** is switched off on purpose. `checkout.py` only imports it when `settings.COUPONS_ENABLED` is on, and that's hard-coded to `False` ("pricing review pending, see #212"). It isn't dead; it's waiting on a decision.
- **`integrations/sheets_sync.py` and `slack_hook.py`** load only if a deployment sets the `LEDGER_PLUGINS` environment variable. The repo can't tell me whether any deployment does. Check the real deployment settings before treating them as dead.

## Built but never reached

**1. Receipts: `notify/receipt.send` → `store/outbox.enqueue` → `jobs/compact_outbox.py`**
- `checkout.py:14` calls `receipt.build(order)` and throws the result away. Nothing ever calls `receipt.send()`, so nothing is added to `outbox.jsonl`. The mailer program that's supposed to send from that file has nothing to send. Customers are almost certainly not getting receipts.
- `compact_outbox` isn't listed in `schedule.json`, so it never runs, and the file it would clean up never gets written anyway.
- **What I'd do:** don't drop this quietly. My reading is that `build` was meant to be `send`. Ask whoever owns the mailer, and check whether `outbox.jsonl` exists in the production data folder.
  - If receipts are wanted: move all three files into a small notifications service, change checkout to call `send`, and schedule `compact_outbox`.
  - If not: delete all three, plus the `build` call in checkout.
  - Either way, decide it before the split. Otherwise you'll carry a broken path into a new service.

**2. `reports/weekly.py`**
- Nothing imports it, and neither the CLI, the admin tool nor cron runs it. The docstring says it's "for the Monday meeting", so someone may run it by hand.
- **What I'd do:** ask whoever runs that meeting.
  - If it's used: make it a real command (`ledger report weekly`), so it's visibly reached and goes with the read side of the split.
  - If it isn't: delete it. It's 10 lines that just total up paid orders, so it's cheap to rewrite later.

## Things the split will surface (confirmed in the code)

- **`schedule.json`'s `cron` field is ignored.** `jobs/runner.py` runs every listed job each time it's invoked, so how often things run depends only on the host's crontab. If that runs nightly, `purge_exports` runs nightly too, not weekly on Sundays as the file says. Check this before turning jobs into separate scheduled tasks.
- **`purge_exports` deletes `export-*.csv` from whatever folder the job runs in,** not from the data folder. Its effect depends on where the job is started, which gets fragile once it's a separate service.
- **The jobs and the outbox import `store.db._path`,** which is meant to be private. Each new service will need its own way to find the storage location, or a small shared module.
- **`ledger-admin reindex` renumbers every order ID.** Anything outside that stores order IDs (Slack posts, the sheet, receipts) would end up pointing at the wrong orders. That matters more once IDs travel between services.