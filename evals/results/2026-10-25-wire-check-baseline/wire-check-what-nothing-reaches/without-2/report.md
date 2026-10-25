I read every file in `fixture/` (about 260 lines) and grepped for every reference. I didn't change anything.

## How the code is reached

There are four ways in. Only the first three are visible from the code itself.

| Way in | How | What it reaches |
|---|---|---|
| `ledger` (`cli:main`) | console script | `commands/add`, `listing`, `checkout`, `export` → `store/db`, `settings`, `notify/receipt.build` |
| `ledger-admin` (`admin:main`) | console script (not in the README) | `admin_tools/reset`, `reindex` |
| `python -m jobs.runner` | host cron, reading `jobs/schedule.json` | `jobs/nightly_backup`, `jobs/purge_exports` |
| `LEDGER_PLUGINS` env var | imported by name at runtime in `cli.py:11-13` | whatever each deployment lists, if anything |

So the core of the product is a JSON-file order store with add/list/checkout/export, two operator commands and two cron jobs.

## Built but not reached

**1. Customer receipts (`notify/receipt.send` → `store/outbox.py`): this looks like a bug, not dead code.**
`commands/checkout.py:14` calls `receipt.build(order)` and throws the result away. `send()` is the only thing that calls `outbox.enqueue()`, and nothing calls `send()`. So nothing ever writes `outbox.jsonl`, and the mailer daemon has nothing to send. Customers probably aren't getting receipts.
→ **Don't drop it.** Ask the owner whether receipts are supposed to go out. If yes, the fix is a one-word change to `receipt.send(order)`, and the outbox becomes the boundary between ledger and the notification service. Write that file format down as a contract before the split. The daemon is outside this repo, so check what it expects.

**2. `jobs/compact_outbox.py`: not scheduled.**
It isn't in `schedule.json`. Since nothing writes the outbox (#1), it would have nothing to do anyway.
→ Its fate depends on #1. If receipts come back, schedule it, and move it to whoever owns the outbox (probably the mailer side, since that side knows what "sent" means). If receipts are really retired, delete it along with `store/outbox.py` and `receipt.send`.

**3. `pricing/coupons.py`: switched off on purpose.**
It's only reached when `settings.COUPONS_ENABLED` is true, and that's hardcoded to `False` ("pricing review pending, see #212"). It's a constant, not an env var, so no deployment can turn it on.
→ Settle #212 before the split rather than carrying the question across. If coupons are coming, keep it with checkout/pricing. If not, delete the module and the branch in `checkout.py:9-11`.

**4. `reports/weekly.py`: nothing reaches it.**
No command, job or import uses it, even though its docstring says it's for the Monday meeting. Someone may be running it by hand with `python -c`.
→ Ask whoever runs that meeting. If it's used, make it a proper `ledger report` command or a scheduled job, so it has a real way in. If nobody claims it, delete it.

**5. `integrations/sheets_sync.py` and `integrations/slack_hook.py`: can't tell from the code, and both are stubs.**
They only load if a deployment's `LEDGER_PLUGINS` lists them, so check the deployment configs or environments. Even if they are enabled, neither does anything real: `sheets_sync` prints "synced to the finance sheet" and `slack_hook` prints `[slack] ...`. Neither calls Sheets or Slack.
→ If no deployment enables them, delete both and the plugin loader with them. If one is enabled, someone believes it works when it doesn't; that's a conversation to have, not code to carry over as-is. A real Slack notification would fit better on the outbox/event path from #1 than on wrapping the checkout command.

## Things reached but worth knowing before you split
- **`jobs/runner.py` ignores the `cron` field.** It runs every listed job on each call. If the host cron runs it nightly, `purge_exports` runs nightly, not weekly as `30 3 * * 0` suggests.
- **`purge_exports` may not delete anything.** It deletes `export-*.csv` in the cron process's working directory, but `ledger export` writes to whatever path the user gives. Check whether it ever removes a file.
- **`jobs/*` and `store/outbox.py` import the private `store.db._path`.** That's hidden coupling to the data folder layout. It will break once these pieces live in different services.
- **`ledger-admin reindex` renumbers order IDs.** Once receipts or any outside system refer to order IDs, that becomes dangerous. Consider retiring it during the split.
- The `name=` parameter on `db.load`/`save` is never used with anything but the default. That's minor; just simplify it when you move the code.

**Questions to answer first:** whether receipts should be going out (#1), how #212 is decided (#3), who runs the weekly report (#4), and what each deployment sets `LEDGER_PLUGINS` to (#5). Most of these "keep or drop" calls depend on those answers more than on the code.