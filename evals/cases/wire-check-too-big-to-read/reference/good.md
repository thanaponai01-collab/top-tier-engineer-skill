Ways in, all run: `depot` (364 commands, found by pkgutil and the @command decorator), `depot-admin`
(compact, reseed), `python -m depot.jobs` (schedule.json: daily_digest, age_stock), the three
exporters by name, and both event handlers paths. 928 of 937 functions ran.

Built but not reached:
| piece | first broken link | what I'd do |
|---|---|---|
| depot/commands/bins_rebalance.py | not registered: run() has no @command decorator, so it is not in `depot help` | register it if wanted, else drop |
| inbound_receive.py::_parse_legacy_asn | never called: inbound-receive uses only _parse_line | drop it |
| notify.send_digest + outbox.enqueue | effect lost: daily_digest calls build_digest and drops the result, so nothing is sent | a bug: call send_digest |
| depot/crossdock.py | never invoked: CROSSDOCK_ENABLED is False | owner decision |
| bin_alerts.on_bin_emptied | not routed: subscribes to bin.emptied, bins-pick publishes bin.empty | rename the event |
| jobs/purge_audit.py | not routed: not in schedule.json | schedule it |

on_bin_low is live (bins-pick publishes f"bin.{state}" with low).
