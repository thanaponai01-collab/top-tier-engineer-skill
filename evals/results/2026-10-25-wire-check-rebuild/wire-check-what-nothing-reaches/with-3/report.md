I ran every entry point the repo declares, in throwaway copies. That covered all four `ledger` commands, both `ledger-admin` commands, the cron job runner, and each plugin turned on through `LEDGER_PLUGINS` the way a deployment would. 18 of the 23 functions were reached. Every one of the other 5 has a recorded reason, and the check passes (`WIRE-GATE: done`). No code changed. The only file written is the skill's report, `fixture/.wire/` (snapshot plus `verdicts.md`).

## What the codebase actually serves

| Way in | What it reaches |
|---|---|
| `ledger add / list / checkout / export` | `commands/*`, `store/db.py` |
| `ledger-admin reset` (needs `--yes`) and `reindex` | `admin_tools/*` |
| `python -m jobs.runner` (host cron) | `nightly_backup`, `purge_exports` (it deleted the export file I made, which is why the last run's `ls` "failed") |
| `LEDGER_PLUGINS=sheets_sync` | adds `ledger sync-sheet` |
| `LEDGER_PLUGINS=slack_hook` | wraps `checkout` to post to Slack |

Both plugins only run when that environment variable is set. Before splitting, check which deployments actually set it.

## What nothing reaches, and what I'd do with each

**1. Customer receipts: built, then thrown away.**
- **What's wrong:** `commands/checkout.py:14` calls `receipt.build(order)` and discards the result, when it should call `receipt.send(order)`. So `notify/receipt.py::send` and `store/outbox.py::enqueue` never run, and no receipt is ever queued for the mailer.
- **What I'd do:** this is the one that matters. The docstrings say receipts are meant to go out, so it's almost certainly a bug, not dead code. Find out from whoever owns the mailer whether customers should be getting receipts. If yes, it's a one-word fix, and it belongs to the notifications service. Don't drop it.

**2. `jobs/compact_outbox.py`: never scheduled.**
- **What's wrong:** `jobs/schedule.json` lists only `nightly_backup` and `purge_exports`, and the runner only runs what that file lists.
- **Why it hasn't mattered:** it would have nothing to do anyway, because the outbox is never written (see item 1). It also depends on the external mailer marking lines `"sent"`.
- **What I'd do:** keep it only if you fix receipts. In that case move it with the outbox into the notifications service and add a schedule entry. If receipts are dropped, delete it.

**3. `pricing/coupons.py`: switched off.**
- **What's wrong:** it's only imported inside the branch at `checkout.py:9`, and `COUPONS_ENABLED = False` (`settings.py:4`, "pricing review pending, see #212").
- **Seen in the run:** `checkout 1 SPRING10` went through at full price.
- **What I'd do:** this is a deliberate hold, not an accident, so the answer depends on #212. If the pricing review is still active, carry it over still switched off, with a pointer to #212. If the review is dead, delete it. Either way, don't let it quietly turn back on in the new service.

**4. `reports/weekly.py`: nothing calls it.**
- **What's wrong:** no command, job or schedule entry mentions it. It's a "weekly revenue summary for the Monday meeting" that nothing produces.
- **What I'd do:** ask whoever runs that meeting whether they still get the number some other way, perhaps the Sheets sync. If nobody misses it, delete it. If they want it, add it as a scheduled job or a `ledger report` command in the reporting service. Don't carry it over unconnected.

## Two smaller things to watch during the split
- `purge_exports` deletes `export-*.csv` from whatever folder cron runs in. `ledger export` writes wherever the user tells it to (the README's example is `<file.csv>`). So the cleanup probably misses most real exports.
- Three files reach into `store.db._path`, a private helper: `compact_outbox`, `nightly_backup` and `outbox`. Once storage becomes its own service, that becomes a dependency across services.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

- notify/receipt.py::send: effect-lost: commands/checkout.py:14 calls receipt.build(order) and discards the message instead of receipt.send(order); no customer receipt is ever queued
- store/outbox.py: effect-lost: only caller is notify/receipt.py:14 (send), which nothing calls; the lost link is commands/checkout.py:14
- jobs/compact_outbox.py: not-routed: the runner only runs jobs listed in jobs/schedule.json:1, which has nightly_backup and purge_exports but not compact_outbox; it would also have nothing to compact since the outbox is never written (commands/checkout.py:14)
- pricing/coupons.py: never-invoked: imported only inside the branch at commands/checkout.py:9, gated by COUPONS_ENABLED = False at settings.py:4 (pricing review #212)
- reports/weekly.py: not-registered: no command, job, or schedule entry names reports.weekly
