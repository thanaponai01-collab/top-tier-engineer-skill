I ran every way into the CLI under a call tracer. **928 of 937 functions are reachable. 7 pieces are never reached.** Some of those are bugs rather than dead code, and that matters for what you port.

## What's reachable
All five declared entry points were run in throwaway copies of the repo, so your `data/` was never touched:

- **`depot` (`cli.py`)**: all 364 registered commands ran without errors. That includes the ones that publish events (`bins-pick`, `inbound-receive`), `export` in csv, json and xml, and `orders-ship`.
- **`depot-admin`**: `compact` and `reseed` both run.
- **`python -m depot.jobs`**: runs `daily_digest` and `age_stock`.
- **Supporting code**: `registry`, `bus`, `store`, `settings`, the `audit` handler and the `bin.low` alert are all reached.

One caveat: "reachable" means a command path exists, not that anyone uses it. 360 of the commands are near-identical generated per-collection commands (`audits-top`, `cycle-zones`, …). To trim those you'd need real usage data, such as shell history or wrapper logs. Tracing can't tell you that.

## Built but not reached

| Piece | Why nothing reaches it | What I'd do |
|---|---|---|
| `commands/bins_rebalance.py` | `run()` has no `@command("bins-rebalance")` decorator, unlike every other command module. `depot bins-rebalance` reports "unknown command". | Ask the floor leads whether they expected it to exist. If yes, port it with the decorator (it's a one-line fix). If nobody noticed it was missing, drop it. |
| `commands/inbound_receive.py::_parse_legacy_asn` | Nothing calls it. Its docstring says it parses the supplier format from before the EDI switch. | Drop it. Only keep it if some supplier still sends that format. |
| `crossdock.py` | Its only caller is behind `settings.CROSSDOCK_ENABLED` (`orders_ship.py:9`). That's hard-coded `False` (`settings.py:5`, "pilot, waiting on the ops review") with no environment override. | Don't port it yet. Get a decision from ops: if the pilot is live, port it with a real config switch; if it's dead, delete it and the `orders_ship` branch. |
| `handlers/bin_alerts.py::on_bin_emptied` | **This is a bug, not dead code.** `bins-pick` publishes `bin.empty` (`bins_pick.py:7,26`) but the handler listens for `bin.emptied` (`bin_alerts.py:16`). In the trace, picking bin 1 down to 0 wrote the "low" note but no "empty, schedule a refill" note. | Port it and fix the event name on the new platform. The floor is meant to get these alerts and currently doesn't. |
| `jobs/purge_audit.py` | Not listed in `jobs/schedule.json`, which is the only thing the job runner reads. The audit log grows with every stock move and is never trimmed. | Port it and schedule it, or replace it with the new platform's log retention. Dropping it means the audit log grows without limit. |
| `notify.py::send_digest` and `outbox.py` | **Another bug.** `daily_digest` builds the low-stock digest and throws the result away (`daily_digest.py:6`) instead of calling `send_digest`, so nothing ever reaches the outbox or the mailer. | Find out whether floor leads still want the nightly email. If yes, port it with the job calling `send_digest`, using the new platform's mailer instead of the outbox file. If no, drop `send_digest`, `outbox.py` and the digest building, and keep only the count line. |

Related to the last row: `daily_digest` is technically reachable, because it runs nightly, but all it actually does is print a line. Don't count it as working.

## Notes
- No code was changed. The skill's records are in `fixture/.wire/`: `snapshot.json` is the trace and `verdicts.md` has one line per unreached piece, citing file and line. The skill's checker passes.
- On this Windows machine the first pass under-counted because of Windows line endings in `depot help` output. I fixed that and reran; the numbers above are from the corrected run.

<!-- file written by the agent: fixture/.wire/verdicts.md -->
# Wire verdicts

- depot/commands/bins_rebalance.py: not-registered: run() has no @command decorator (every other command module has one, cf. depot/commands/bins_pick.py:13), so registry.all_commands imports it but never maps a name to it; `depot bins-rebalance` is "unknown command"
- depot/commands/inbound_receive.py::_parse_legacy_asn: not-registered: no caller anywhere; run() only parses `sku:qty` via _parse_line (depot/commands/inbound_receive.py:21); docstring says pre-EDI format
- depot/crossdock.py: never-invoked: only caller is behind `if settings.CROSSDOCK_ENABLED` (depot/commands/orders_ship.py:9), hard-coded False with no env override (depot/settings.py:5)
- depot/handlers/bin_alerts.py::on_bin_emptied: not-routed: subscribes "bin.emptied" (depot/handlers/bin_alerts.py:16) but bins-pick publishes f"bin.{state}" with state "empty" (depot/commands/bins_pick.py:7,26) -> event "bin.empty", no subscriber; seen in snapshot: picking bin 1 to 0 wrote no floor note
- depot/jobs/purge_audit.py: not-registered: job module exists but is not listed in depot/jobs/schedule.json ("daily_digest", "age_stock"), which is the only thing depot/jobs/__main__.py:10 runs
- depot/notify.py::send_digest: effect-lost: daily_digest builds the digest and discards it (depot/jobs/daily_digest.py:6) instead of calling send_digest, so nothing is ever queued
- depot/outbox.py: effect-lost: only caller is notify.send_digest (depot/notify.py:11), itself never called because depot/jobs/daily_digest.py:6 drops the digest
