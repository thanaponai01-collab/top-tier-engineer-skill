I read all ~260 lines. The repo has three entry points: `ledger` (`cli:main`), `ledger-admin` (`admin:main`), and `python -m jobs.runner`, which the code says the host's cron runs. I couldn't see the crontab or any deployment environment, so anything that depends on them is marked as unconfirmed.

## What the codebase serves

| Entry point | Reaches |
|---|---|
| `ledger add / list / checkout / export` | `commands/*`, `store/db.py`, `settings.py` |
| `ledger-admin reset / reindex` | `admin_tools/*`. It isn't in the README but `pyproject.toml` installs it. |
| `jobs.runner` (cron) | `nightly_backup`, `purge_exports` (the jobs listed in `schedule.json`) |
| `LEDGER_PLUGINS=…` (environment variable) | `integrations/sheets_sync`, `integrations/slack_hook`. These only run if a deployment sets the variable, and I can't see whether any does. |

That's the real product: a JSON-file order store with four user commands, two admin commands and two cron jobs.

## What's built but nothing reaches

**1. Customer receipts: `notify/receipt.py`, `store/outbox.py`, `jobs/compact_outbox.py`.** This matters most, because it looks like a bug rather than leftover code.
- `commands/checkout.py:14` calls `receipt.build(order)` and throws away the result. It never calls `receipt.send()`, so `outbox.enqueue()` never runs and nothing writes `outbox.jsonl`. No receipt has ever reached the mailer daemon from this code.
- `compact_outbox` isn't in `schedule.json` and nothing imports it. It cleans up a file that never gets written.
- **What I'd do:** ask whoever owns the mailer daemon whether customers are supposed to get receipts. If yes, it's a one-line change to `send()` plus adding `compact_outbox` to the schedule. But that turns on customer email, so it should be its own decision, not something that slips in during the split. If nobody has noticed receipts missing, delete all three files and don't carry the outbox over.

**2. `reports/weekly.py`.** Nothing imports it and there's no command for it, even though its docstring says it's "for the Monday meeting".
- **What I'd do:** find out whether anyone runs it by hand. If they do, give it a real command (for example `ledger report weekly`) in whichever service owns reads. If not, drop it.

**3. `pricing/coupons.py`.** This one is switched off on purpose, not abandoned. It's reached only when `settings.COUPONS_ENABLED` is true, and that's hard-coded to `False` ("pricing review pending, see #212").
- **What I'd do:** move it with checkout and keep it switched off if #212 is still open. If #212 is closed or abandoned, delete it along with the flag.

**4. `integrations/*`.** These can be reached, but both are stubs. `sheets_sync` only prints "synced to the finance sheet" and `slack_hook` only prints `[slack] …`. Neither talks to Sheets or Slack.
- **What I'd do:** check the real `LEDGER_PLUGINS` value in each deployment. If it's unset, delete both and the plugin loader in `cli.py`. If it's set, someone believes these work and they don't, which is worth telling them.

## Other things to know before the split

- **The `cron` fields in `jobs/schedule.json` are ignored.** `jobs/runner.py` runs every job each time it's called, so the host's cron timing is what actually controls when jobs run. If cron runs nightly, `purge_exports` runs nightly, not weekly on Sunday as the file suggests.
- **`purge_exports` may not delete anything, or may delete the wrong files.** It looks for `export-*.csv` in cron's working directory, not in `DATA_DIR`, and `ledger export` writes wherever the user tells it to. Check what it actually deletes before deciding whether it's worth keeping.
- **`ledger-admin reindex` renumbers order ids.** That breaks any id already in an export or receipt. It doesn't matter today, but it will once ids are passed between services.

I made no changes to the code.