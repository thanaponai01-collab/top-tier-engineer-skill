I ran wire-check on `fixture/` and the gate passed (`WIRE-GATE: done`). I started all 5 declared ways in: `ledger`, `ledger-admin`, `python cli.py`, `python admin.py` and the job runner. The two plugins ran with `LEDGER_PLUGINS=sheets_sync,slack_hook` set. Together those runs entered 18 of the 23 functions, and I explained each of the other 5 in `.wire/verdicts.md`.

## What the codebase actually serves

- **`ledger` CLI** (`cli.py`): `add`, `list`, `checkout`, `export`, all working against `store/db.py`.
- **`ledger-admin`** (`admin.py`): `reset` (asks for `--yes` first) and `reindex`.
- **Cron runner** (`python -m jobs.runner`): `nightly_backup` and `purge_exports`. These are the only two jobs in `jobs/schedule.json`.
- **Plugins, only on deployments that set `LEDGER_PLUGINS`**: `sheets_sync` (adds `ledger sync-sheet`) and `slack_hook` (wraps checkout). Both work when enabled. Nothing in the repo shows which deployments turn them on, so check that before deciding which service owns them.

## What got built that nothing reaches

**1. Customer receipts: `notify/receipt.py::send` → `store/outbox.py::enqueue` (built but its effect is lost).** This is a bug, not dead code. At `commands/checkout.py:14`, checkout calls `receipt.build(order)` and throws away the message it returns. It should call `receipt.send(order)`. I ran a real checkout and only `orders.json` was written: no `outbox.jsonl` ever appears, so the mailer daemon has nothing to send. Customers aren't getting receipts.
**What I'd do:** carry it over and fix the call (a one-line change). Before that, confirm the mailer daemon outside this repo still exists. If it doesn't, delete `send`, `outbox.py` and item 2 together.

**2. `jobs/compact_outbox.py` (never registered).** It isn't in `schedule.json` and nothing imports it. It also has no work to do, because nothing writes the outbox (item 1).
**What I'd do:** it belongs to receipts, so its fate follows theirs. If receipts get fixed, move it into the notifications service and add it to that service's schedule. If receipts go, delete it.

**3. `pricing/coupons.py` (turned off by a flag).** `checkout.py:9` only applies coupons when `settings.COUPONS_ENABLED` is on, and `settings.py:4` hard-codes it to `False` ("pricing review pending, see #212"). The README still documents `checkout <order-id> [coupon]`, so the argument is silently ignored: `ledger checkout 1 SPRING10` charged the full 100.00.
**What I'd do:** don't build a pricing service around it. Keep it as a small module next to checkout until #212 is decided. If the answer is no, delete it and drop `[coupon]` from the README. Either way, a coupon code that's accepted and ignored should become an error.

**4. `reports/weekly.py` (never registered).** No command, job or import mentions it. It's an 11-line summary "for the Monday meeting".
**What I'd do:** ask whoever runs that meeting whether they still use it. If not, delete it. If they do, they're getting it some way outside this repo, so wire it in as a command (e.g. `ledger report weekly`) or a job so it doesn't get lost in the split.

## Notes

- `purge_exports` deletes `export-*.csv` from whatever directory cron runs in, but `ledger export` writes to any path the user gives it. Whether the purge actually catches the exports depends on how the host sets up cron.
- I didn't change any source code. The check did write `.wire/` (the run record and `verdicts.md`) inside `fixture/`. The skill suggests committing it alongside changes; delete it if you don't want it.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

- jobs/compact_outbox.py: not-registered: jobs/schedule.json:1-4 lists only nightly_backup and purge_exports; nothing else imports jobs.compact_outbox
- notify/receipt.py: effect-lost: commands/checkout.py:14 calls receipt.build(order) and discards the returned message instead of receipt.send(order); no outbox.jsonl is ever written
- pricing/coupons.py: never-invoked: commands/checkout.py:9 gates it on settings.COUPONS_ENABLED, hard-coded False at settings.py:4 (#212); `ledger checkout 1 SPRING10` charges 100.00
- reports/weekly.py: not-registered: no CLI command, admin command, schedule.json entry or import names reports.weekly
- store/outbox.py: never-invoked: its only caller is notify/receipt.py:14 (send), which commands/checkout.py:14 never calls
- notify/receipt.py::send: effect-lost: commands/checkout.py:14 calls receipt.build(order) and discards the returned message instead of receipt.send(order); no outbox.jsonl is ever written
- reports/weekly.py: [[fill: served | not-registered | not-routed | never-invoked | effect-lost | unknown]]: [[fill: why, with the file:line]]
