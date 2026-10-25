# Wire check: depot (`fixture/`)

I ran every way into the CLI in a throwaway copy:

- all 364 registered `depot` commands, plus `help` and an unknown command;
- the three `export` formats (csv, json, xml);
- `bins-pick` three times: once to leave a bin low, once to empty one, and once asking for more than the bin holds;
- `inbound-receive`, `orders-ship`, both `depot-admin` tools, and `python -m depot.jobs`.

All the runs finished and the helper's gate passed (`WIRE-GATE: done`). Of 937 functions, 928 ran. The other 9, across 7 places, are listed below. The code is unchanged; the only thing I wrote is the helper's record in `fixture/.wire/` (`snapshot.json` and `verdicts.md`).

## Reachable: port these

- **The `depot` CLI**: `cli.py` and `registry.py`, plus 364 commands. That's 12 read-only verbs (list, show, search, count, top, newest, oldest, stats, summary, tags, zones, check) for each of 30 record types. They're near-identical generated code, so on the new platform I'd write them as one generic command that takes the verb and record type, not 360 files. Add `bins-pick`, `inbound-receive`, `orders-ship` and `export`. All three export formats ran.
- **Events**: `bus.py`, `handlers/audit.py` (runs on every stock move) and `bin_alerts.on_bin_low`.
- **`depot-admin`**: `compact` and `reseed`.
- **Nightly jobs**: `age_stock` and `daily_digest`. But `daily_digest` does nothing useful today (see item 1).
- **Storage**: `store.py` and `settings.py`.

## Built but nothing reaches it

1. **`notify.send_digest` and `outbox.py`: the result is thrown away.** `depot/jobs/daily_digest.py:6` builds the digest and discards it instead of calling `send_digest`, so nothing is ever queued for the mailer. The nightly job only prints a count. **What I'd do:** check with whoever expects the "N bins low" email. If they want it, port all of this and change that line to call `send_digest`. That's a real bug fix, not leftover code. If not, drop `notify.py`, `outbox.py` and the digest job.

2. **`bin_alerts.on_bin_emptied`: event name mismatch.** It listens for `"bin.emptied"` (`handlers/bin_alerts.py:16`), but `bins-pick` sends `"bin.empty"` (`commands/bins_pick.py:7,26`). I emptied bin 2 in the run and no "schedule a refill" note appeared. **What I'd do:** port it and fix the name on one side. The low-stock alert next to it works, so the empty-bin alert was clearly meant to work too.

3. **`commands/bins_rebalance.py`: never registered as a command.** It's missing the `@command("bins-rebalance")` line (`:9`), so `depot bins-rebalance` reports "unknown command". **What I'd do:** ask ops whether they want it. It's finished code that was simply never added to the command list. If nobody has missed it, leave it behind.

4. **`jobs/purge_audit.py`: not in the nightly schedule.** It isn't listed in `jobs/schedule.json`. Meanwhile `handlers/audit.py` adds to the audit log on every stock move, so that file grows forever. **What I'd do:** port it and add it to the schedule, or let the new platform handle log rotation. Either way, something needs to cap that file.

5. **`crossdock.py`: switched off.** It only runs when `settings.CROSSDOCK_ENABLED` is on (`commands/orders_ship.py:9`). That's hard-coded to `False` (`settings.py:5`) with no environment variable to change it, and the comment says it's a pilot "waiting on the ops review". **What I'd do:** don't port it now. Keep it in version history and bring it back as a proper setting if the ops review approves it.

6. **`inbound_receive._parse_legacy_asn`: nothing calls it.** Its docstring says it handles the supplier format from before the EDI switch. **What I'd do:** delete it and don't port it.

Items 1, 2 and 4 are bugs in code that's otherwise in use, not dead features. Decide on those before the port. If they're ported as they are, the new platform will repeat the same silent failures.

The full list with file and line references is in `fixture/.wire/verdicts.md`.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

One line per function (or whole file) no snapshot command entered:
`- <file>[::<function>]: <class>: <why>`. Classes: served (reached by a way in that cannot run
here; cite the file:line that reaches it), not-registered (nothing names it), not-routed (registered,
but no trigger maps to it; cite where it should be), never-invoked (a flag or branch nobody takes;
cite it), effect-lost (it runs, or should, but its result is dropped; cite the line), unknown
(depends on something outside the repo; say what). A declared way in you could not start:
`- entry <name>: not run: <why>`.

- depot/commands/bins_rebalance.py: not-registered: run() has no @command("bins-rebalance") decorator (depot/commands/bins_rebalance.py:9), so registry.all_commands() imports the module but never adds it; `depot bins-rebalance` -> "unknown command"
- depot/commands/inbound_receive.py::_parse_legacy_asn: not-registered: no caller anywhere; inbound-receive parses only via _parse_line (depot/commands/inbound_receive.py:21); docstring says pre-EDI format
- depot/crossdock.py: never-invoked: only reached under `if settings.CROSSDOCK_ENABLED` (depot/commands/orders_ship.py:9), hardcoded False with no env override (depot/settings.py:5)
- depot/handlers/bin_alerts.py::on_bin_emptied: not-routed: subscribes "bin.emptied" (depot/handlers/bin_alerts.py:16) but bins-pick publishes f"bin.{state}" with state "empty" -> "bin.empty" (depot/commands/bins_pick.py:7,26); `bins-pick 2 17` emptied bin 2 and the handler did not run
- depot/jobs/purge_audit.py: not-routed: not listed in the nightly schedule (depot/jobs/schedule.json:1 has only daily_digest, age_stock), which is the only thing depot/jobs/__main__.py:9 runs
- depot/notify.py::send_digest: effect-lost: daily_digest calls build_digest and discards the result instead of send_digest (depot/jobs/daily_digest.py:6), so no digest ever reaches the outbox
- depot/outbox.py: not-routed: only caller is notify.send_digest (depot/notify.py:11), which nothing calls (depot/jobs/daily_digest.py:6)
