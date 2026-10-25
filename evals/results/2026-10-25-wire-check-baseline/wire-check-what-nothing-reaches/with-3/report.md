I couldn't run a git status check because `fixture/` isn't a git repo. The runs used a throwaway data directory and working directory, so nothing in `fixture/` changed.

# What this codebase actually serves and what nothing reaches

**The first break:** paying for an order never produces a customer receipt. `checkout` calls `receipt.build(order)` at `commands/checkout.py:14` and throws away the message it returns. `receipt.send()` is the only thing that puts a message in the queue for the mailer, and nothing calls it. After a checkout, `data/` held only `orders.json` and no `outbox.jsonl` (proven by running it). This looks like dead code but it's a live bug.

## Ways in

| Entry | Instances | Status |
|---|---|---|
| `ledger` command (`pyproject.toml` → `cli:main`) | add, list, checkout, export | proven |
| `ledger-admin` command (`admin:main`) | reset, reindex | proven (reindex run; reset traced, same dispatch) |
| Host cron → `python -m jobs.runner` | entries in `jobs/schedule.json` | runner proven; **whether cron is installed is UNKNOWN** (only the docstring says so) |
| Plugins loaded by name from `LEDGER_PLUGINS` | `slack_hook`, `sheets_sync` | **UNKNOWN**: they work when the variable is set (proven), but per-deployment settings aren't in the repo |
| An outside reader: the mailer daemon reads `outbox.jsonl` | — | outside this repo; UNKNOWN |

## Served vs. unreached

I listed every function in the source first, then ran each entry point with a tracer to see which functions actually executed. The unreached set is the first list minus the second.

| Piece | Status | First broken link | Evidence | What I'd do |
|---|---|---|---|---|
| `commands/*`, `store/db.py`, `settings.py`, `cli.py` | served | — | proven | Carry over; this is the core order service. |
| `admin.py`, `admin_tools/*` | served | — | proven | Carry over as operator tooling. Be aware `reindex` renumbers order IDs, which breaks any external reference to an order once it's a separate service. |
| `jobs/runner.py`, `nightly_backup`, `purge_exports` | served if cron runs | — | proven | Carry over, but fix the two problems below before splitting. |
| **`notify/receipt.send` + `store/outbox.py`** | **effect lost** | 5 Reachable | proven | **Live bug, not dead weight.** Fix it by having `checkout` call `receipt.send(order)` instead of `build`. Then make it the notification service's interface. Don't delete it. |
| **`pricing/coupons.py`** | never invoked | 4 Invoked: `COUPONS_ENABLED = False` (`settings.py:4`, "#212") | proven | **Your call, as the owner.** It's parked on a pricing review. Note that `checkout 1 VIP25` silently charged 100.00 with no warning, so customers who enter codes are ignored without being told. Either resolve #212 and move it into pricing, or delete it and stop accepting the coupon argument. |
| **`jobs/compact_outbox.py`** | orphaned | 2 Registered: not in `schedule.json` | traced | Only needed once the outbox exists. Hold it until the receipt fix lands, then add it to the schedule. Otherwise delete it. |
| **`reports/weekly.py`** | orphaned | 2 Registered: nothing imports it, and there's no command or job for it | traced (grep + run) | "For the Monday meeting" suggests someone may run it by hand. Ask whoever runs it. If nobody does, delete it. If someone does, add it as a `ledger report` command. |
| `integrations/slack_hook.py` | UNKNOWN (only via the environment variable) | 1 Exists: it's a stub | proven | It only `print`s `[slack] …` and never posts to Slack. Check the deployment configs. Even where it's enabled, it does nothing real. Rebuild it as a consumer of order-paid events in the new design, or drop it. |
| `integrations/sheets_sync.py` | UNKNOWN (only via the environment variable) | 1 Exists: it's a stub | proven | Same: it prints "synced to the finance sheet" and syncs nothing. Drop it unless finance relies on a real sync that lives elsewhere. |

## Two problems found in served code (they matter for the split)
- **`purge_exports` deleted a real export.** Running the scheduler removed `export-1.csv`, which `ledger export` had just written, along with anything else named `export-*.csv` in the current directory of whatever cron happens to run in. `mine.csv` survived only because of its name.
- **The runner ignores the `cron` field.** Every run executes every job in the list, so the "weekly" purge runs whenever the nightly backup does. The `cron` strings in `schedule.json` do nothing.

## The connecting code (not applied, since you asked for a report only)
```python
# commands/checkout.py:14
-    receipt.build(order)
+    receipt.send(order)
```

## Recommendation
Before the split, add one smoke test per entry point that runs it the way a user would and checks the result. For example: run `ledger checkout`, then assert that `outbox.jsonl` contains the receipt. Also add a CI check that fails when a module under the packages listed in `pyproject.toml` isn't reachable from `cli`, `admin` or `schedule.json`. Modules that are allowed to be unreached (plugins, parked features) go on an allowlist so they're kept on purpose.

Still unknown and only provable outside this repo: the host crontab, each deployment's `LEDGER_PLUGINS`, and whether the mailer daemon exists. If you can share the crontab or `crontab -l` and the deployment environment files, I'll close those out.