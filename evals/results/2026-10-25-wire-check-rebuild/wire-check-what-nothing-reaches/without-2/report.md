I read all 31 files. This is a small codebase, about 260 lines.

## What it serves

There are three real entry points: the two console scripts in `pyproject.toml` and the host cron job.

| Entry point | What it reaches |
|---|---|
| `ledger` (`cli.py`) | `add`, `list`, `checkout`, `export`, all on top of `store/db.py` and `settings.py` |
| `ledger-admin` (`admin.py`) | `reset`, `reindex` |
| Host cron: `python -m jobs.runner` | the jobs listed in `jobs/schedule.json`: `nightly_backup` and `purge_exports` |
| `LEDGER_PLUGINS` env var (loaded by name at runtime) | `integrations/sheets_sync.py` (adds `sync-sheet`) and `integrations/slack_hook.py` (wraps `checkout`) |

The plugins are only reachable if a deployment sets `LEDGER_PLUGINS`. I can't see any deployment config from the repo, so I don't count them as dead. Check each deployment's environment before deciding about them.

## Built but not reached

**1. `reports/weekly.py`: nothing imports it.** No command, admin tool or job calls it, even though its docstring says it's "for the Monday meeting." Either someone runs it by hand (`python -c ...`), or it's abandoned.
→ Ask whoever runs the Monday meeting. If they use it, make it a real command (`ledger report weekly`) in whichever service owns reads. If not, drop it. Don't carry it over as an unattached module.

**2. `notify/receipt.send()` and `store/outbox.py`: never called, which means receipts are silently not sent.** `checkout.py:15` calls `receipt.build(order)` and throws away the result. Nothing calls `receipt.send()`, so `outbox.enqueue()` never runs and `outbox.jsonl` is never written. The docstring says an outside mailer daemon reads that file, so that daemon is currently getting nothing. This looks like a bug, not leftover code: `checkout` almost certainly meant to call `send`.
→ Decide this before the split, not during it. If customers should get receipts, the fix is a one-line change from `build` to `send`, and the outbox becomes a real contract between the ledger and the mailer. That contract matters a lot for where you draw service boundaries. If receipts were dropped on purpose, remove `notify/` and `store/outbox.py` together and confirm the mailer daemon can be retired.

**3. `jobs/compact_outbox.py`: not in `schedule.json`, so the runner never runs it.** It would have nothing to do anyway, because of item 2.
→ It depends on item 2. If receipts come back, schedule it and move it to whichever service owns the outbox. Otherwise delete it.

**4. `pricing/coupons.py`: reachable in code, but switched off.** `settings.COUPONS_ENABLED = False` is hard-coded (not read from an env var) and marked "pricing review pending, see #212." No deployment can turn it on without a code change.
→ It isn't dead; it's parked. Check the status of #212. If the review is still alive, keep it with checkout and make the flag configurable. If #212 is closed or stale, remove the module and the flag.

## Other issues that affect the split

- **`schedule.json`'s `cron` fields are ignored.** `jobs/runner.py` runs every listed job each time the host cron fires. If that cron fires nightly, `purge_exports` (meant to run Sundays at 03:30) runs every night. Find the real crontab before you split the jobs out. It isn't in the repo.
- **`purge_exports` deletes `export-*.csv` in whatever directory cron runs in.** `ledger export` writes to any path the user gives. So the job only finds files whose names and location happen to match.
- **`ledger-admin reindex` renumbers order IDs.** Anything outside that holds an order ID would end up pointing at the wrong order: Slack posts, the finance sheet, and receipts once they work. If orders move to their own service with stable IDs, I'd retire this command instead of porting it.

I haven't changed anything. If it helps, I can draft the one-line receipt fix or a proposed service map as a separate step.