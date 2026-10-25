Almost all of it is reachable: 928 of the 937 functions ran when I started the real entry points. The other 9 sit in 7 pieces, and only 2 of those are truly dead. The rest were meant to be connected and are broken, and they look like bugs in production now. The gate passed (`WIRE-GATE: done`). I didn't change any code; the only thing I wrote is the evidence in `fixture/.wire/` (`snapshot.json` and `verdicts.md`).

## How I checked

I ran every entry point in a throwaway copy and recorded which functions each run entered. That was 374 runs:
- each of the 364 registered `depot` commands, plus `help` and an unknown command;
- `export` in csv, json and xml (the exporter module is picked by name at runtime, so each format needed its own run);
- `orders-ship` and `inbound-receive`;
- `bins-pick` three ways: leaving the bin low, emptying it, and asking for more than it holds;
- `depot-admin compact`, `reseed`, and running it with no tool given;
- `python -m depot.jobs`.

"Reachable" here means a real command enters the code. It doesn't tell you which commands people actually use. If you want to trim further, you'd need usage logs from the current deployment.

## Reachable (port these)

- **The `depot` CLI:** all 364 commands, the 31 groups like `bins-*`, `orders-*` and `audits-*`, plus `export` (csv/json/xml), `orders-ship`, `inbound-receive` and `bins-pick`.
- **Event handlers:** `stock.moved` writes the audit log and `bin.low` writes a floor note.
- **`depot-admin`:** `compact` and `reseed`.
- **Nightly jobs:** `daily_digest` and `age_stock`.
- **Shared code:** `store`, `settings`, `registry`, `bus`, `exporters`.

## Built but never reached, and what I'd do with each

| Piece | Why nothing reaches it | What I'd do |
|---|---|---|
| `depot/handlers/bin_alerts.py::on_bin_emptied` | `bins-pick` sends the event `bin.empty` (`depot/commands/bins_pick.py:7`), but the handler listens for `bin.emptied` (`bin_alerts.py:16`). When `bins-pick 1 10` empties a bin, no "schedule a refill" note is written. | **Fix and port.** It's a one-word name mismatch, and the floor isn't getting empty-bin alerts today. |
| `depot/notify.py::send_digest` and `depot/outbox.py` | The nightly job builds the digest and then drops it (`depot/jobs/daily_digest.py:6`) instead of calling `send_digest`. Nothing ever reaches the outbox, so the mailer gets nothing. | **Fix and port** if floor leads are supposed to get the digest; the job's output line suggests they are. Check that the new platform's mailer reads the outbox file, since that daemon is outside this repo. |
| `depot/jobs/purge_audit.py` | `python -m depot.jobs` only runs the jobs listed in `schedule.json:1` (`daily_digest`, `age_stock`), and this one isn't listed. | **Port it and schedule it.** Without it the audit log, which every stock move appends to, grows forever. Ask ops first whether it was left out on purpose. |
| `depot/commands/bins_rebalance.py` | Its `run()` has no `@command(...)` decorator, so the registry never adds it and `depot bins-rebalance` says "unknown command". | **Ask the owner.** Nobody can have been using it. If it's wanted, it needs one decorator line and a test. If not, drop it. |
| `depot/crossdock.py` | It's only used behind `settings.CROSSDOCK_ENABLED`, which is hard-coded `False` (`settings.py:5`, "pilot, waiting on the ops review"). | **Don't port now.** Leave it behind and record where it hooks into `orders_ship.py:9`. Bring it across if the ops review approves the pilot. |
| `depot/commands/inbound_receive.py::_parse_legacy_asn` | Nothing calls it. `inbound-receive` only uses `_parse_line`, and its docstring says it's the format from before the EDI switch. | **Drop it.** Confirm no supplier still sends the old fixed-width format. |

Only the last two are truly dead. The first three are features that were meant to be connected and aren't (empty-bin alerts, the nightly digest email, audit log trimming). Fix those during the port rather than leaving them out.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

- depot/commands/bins_rebalance.py: not-registered: run() has no @command(...) decorator, so registry.all_commands() (depot/registry.py:15) imports the module but never adds it; `depot bins-rebalance` answers 'unknown command'
- depot/commands/inbound_receive.py::_parse_legacy_asn: not-registered: nothing calls it; inbound-receive only uses _parse_line (depot/commands/inbound_receive.py:21); docstring says it predates the EDI switch
- depot/crossdock.py: never-invoked: only imported inside `if settings.CROSSDOCK_ENABLED:` (depot/commands/orders_ship.py:9) and the flag is hard-coded False (depot/settings.py:5)
- depot/handlers/bin_alerts.py::on_bin_emptied: effect-lost: bins-pick publishes 'bin.empty' (depot/commands/bins_pick.py:7 + :26) but the handler subscribes 'bin.emptied' (depot/handlers/bin_alerts.py:16); `depot bins-pick 1 10` empties the bin and no floor note is written
- depot/jobs/purge_audit.py: not-routed: python -m depot.jobs runs only the names in depot/jobs/schedule.json:1 (daily_digest, age_stock); purge_audit is not listed
- depot/notify.py::send_digest: effect-lost: the nightly digest job calls build_digest and drops the result (depot/jobs/daily_digest.py:6) instead of send_digest, so no message reaches the outbox
- depot/outbox.py: effect-lost: only caller is notify.send_digest (depot/notify.py:11), which nothing calls because depot/jobs/daily_digest.py:6 discards the built digest; mailer daemon reading outbox is outside this repo
