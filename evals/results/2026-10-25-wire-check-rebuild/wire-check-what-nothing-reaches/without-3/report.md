The ledger has three ways in, and every live code path starts from one of them. Four pieces of code are built but never reached. The most important is the customer receipt pipeline, which looks broken rather than unwanted. I read every file and traced the imports by hand. I didn't run anything or change any code.

## What the codebase actually serves

| Entry point | How it's reached | What it uses |
|---|---|---|
| `ledger` (`cli:main`) | console script in `pyproject.toml` | `commands/add`, `listing`, `checkout`, `export` → `store/db` |
| `ledger-admin` (`admin:main`) | console script | `admin_tools/reset`, `reindex` → `store/db` |
| `python -m jobs.runner` | the host's cron (per its docstring) | `jobs/nightly_backup`, `jobs/purge_exports` (listed in `schedule.json`) |
| `integrations/sheets_sync`, `slack_hook` | loaded by name from the `LEDGER_PLUGINS` env var (`cli.py:11-13`) | `sheets_sync` adds a `sync-sheet` command; `slack_hook` wraps `checkout` |

You can't tell from the repo whether the two integrations are used. They're only switched on by each deployment's environment, so a code search shows them as unused even if production relies on them. Check the deployment config before you decide anything about them. My guess is they're live.

## What got built that nothing reaches

**1. The customer receipt pipeline: `notify/receipt.send`, `store/outbox.py` and `jobs/compact_outbox.py`.** This is the important one.
- `commands/checkout.py:14` calls `receipt.build(order)` and throws away the result. Nothing ever calls `receipt.send`, so nothing is written to `outbox.jsonl`.
- That means `store/outbox.enqueue` is never called. `compact_outbox` isn't in `schedule.json`, so the job runner never runs it either.
- The docstrings say a separate mailer program reads that outbox. So customers are probably not getting receipts today.
- This looks like a bug, not a feature someone abandoned: `build` was almost certainly meant to be `send`.
- **What I'd do:** don't delete it, and don't carry it over without a decision. Ask whoever owns receipts whether they're supposed to be going out.
  - If yes: change the call to `receipt.send(order)` and add `compact_outbox` to the schedule, or the outbox will grow forever.
  - If no: drop all three files, and make sure nothing still expects that mailer to have work.
  - Either way, the outbox is a natural boundary between services. Receipts and the outbox belong in a notification service, not in orders.

**2. `reports/weekly.py`.** Nothing imports it: no command, no job, no script. Its docstring says it's "for the Monday meeting".
- **What I'd do:** ask whoever runs that meeting whether they still use it, perhaps by running it by hand from a Python shell. If not, drop it. If so, give it a real entry point, such as a `ledger report` command or a scheduled job, in whichever service ends up owning reporting.

**3. `pricing/coupons.py`.** The code is reachable but switched off. `settings.COUPONS_ENABLED = False` is hard-coded, with a note saying a pricing review is pending (#212). The code is wired up correctly behind that switch.
- **What I'd do:** keep it. Whether it stays depends on #212, not on cleanup. If #212 is dead, drop the module and the flag. Don't carry a hard-coded `False` into a new service without someone owning that decision.

**4. The `"cron"` field in `jobs/schedule.json`.** `jobs/runner.py` reads only `entry['job']` and runs every job each time it's invoked. The listed times (02:00 daily, 03:30 Sundays) do nothing; whatever cron the host has decides when everything runs.
- **What I'd do:** either make the runner respect the field, or delete it and give each job its own host cron entry. Don't carry over a setting that looks like it controls timing but doesn't.

## Reached, but probably not doing its job

- **`jobs/purge_exports.py`** deletes `export-*.csv` from whatever directory cron runs it in. But `ledger export` writes to any path the user types, with no `export-` naming rule. So the purge probably matches nothing. Worse, if cron's directory happens to hold unrelated `export-*.csv` files, it deletes them. Before migrating it, find out where exports actually end up. Either point the job there (ideally inside `LEDGER_DATA`) or drop it.
- **`admin_tools/reindex.py`** renumbers every order ID. That breaks anything outside the ledger that kept an old ID: the sheet, Slack messages, or receipts if they get fixed. This is fine as one tool in one repo. Once you split into services, it becomes dangerous, so I'd retire it or tightly limit who can run it.

## Shared code to plan around

`store/db._path` is a private helper, but `outbox.py`, `compact_outbox.py` and `nightly_backup.py` all import it. Whichever service owns the data folder needs to expose that properly, or each service needs its own storage location.