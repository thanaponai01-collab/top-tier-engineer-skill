Most of the codebase is reachable. Seven pieces aren't, and two of them look like bugs rather than leftovers. I traced the four entry points (`depot`, `depot-admin`, `python -m depot.jobs` and the import-time handler registration), statically checked every module and helper, and ran the CLI against a throwaway data directory to confirm the suspicious paths. I changed nothing.

## Reachable (port these)

- **`depot` CLI** (`cli.py`, `registry.py`): `registry.all_commands()` imports every module in `depot/commands/`, so any module that has `@command(...)` is live. `depot help` lists **364 commands**:
  - the 30 collections × 12 generated verbs (check, count, list, newest, oldest, search, show, stats, summary, tags, top, zones);
  - `bins-pick`, `inbound-receive`, `orders-ship`, and `export`, which is registered from `report_export.py`.
- **Exporters**: `export <collection> <fmt>` picks the module by name at runtime, so `csv`, `json` and `xml` are all reachable. I checked `export bins xml` and it works.
- **Event handlers**: `cli.py` imports `depot.handlers`, which subscribes `audit.record` (to `stock.moved`) and `bin_alerts.on_bin_low` (to `bin.low`). Both fire in practice.
- **`depot-admin`**: `compact`, `reseed`.
- **Nightly jobs**: `schedule.json` lists only `daily_digest` and `age_stock`.
- **Core**: `store`, `settings`, `bus`, and `notify.build_digest`.

## Built but nothing reaches it

| Piece | Why it's unreached | What I'd do |
|---|---|---|
| **`handlers/bin_alerts.on_bin_emptied`** | `bins_pick.py` publishes `f"bin.{state}"` with `state == "empty"`, which makes the event `bin.empty`. The handler subscribes to `bin.emptied`. I picked two bins down to 0 and `floor.json` only got the "low" line, never "schedule a refill". | **This is a bug, not dead code.** The floor clearly expects refill notices. Fix the event name when you port (use one constant for both sides) and keep the handler. |
| **`notify.send_digest` + `outbox.py`** | `jobs/daily_digest.py` calls `build_digest(rows)` and throws the result away. Nothing calls `send_digest`, so nothing is ever queued. After `python -m depot.jobs` there was no `outbox.json`. | **This is probably a bug too.** The docstring says the digest is "for the mailer daemon". Check with ops whether floor leads expect a nightly email. If yes, port it with the job calling `send_digest`. If nobody misses it, drop all three pieces together. |
| **`jobs/purge_audit.py`** | It isn't in `schedule.json`. Meanwhile `handlers/audit.py` appends to the audit log on every stock move, so the log only grows. | Port it and schedule it (or use the new platform's log retention instead). Right now the log grows without limit. |
| **`commands/bins_rebalance.py`** | It has no `@command` decorator, so it never registers and doesn't appear in `depot help`. | Ask whether anyone wanted it. It's complete code that looks like it was meant to ship. If it's wanted, port it with the decorator (and note it moves stock without publishing `stock.moved`, so it would skip the audit log). If not, delete it. |
| **`crossdock.py`** | It's only imported from `orders-ship` behind `settings.CROSSDOCK_ENABLED = False`, which is commented as "waiting on the ops review". | Don't port it now. Keep it in the old repo's history and bring it over only if the pilot is approved. A dormant flag isn't worth carrying to a new platform. |
| **`inbound_receive._parse_legacy_asn`** | Nothing calls it. Its docstring says the format is from "before the EDI switch". | Delete it. It's superseded and there's no path to it. |

## Not code issues, but worth noting for the port

- `handlers/audit.py` writes JSON-lines into `audit.json`, because `_path` always adds `.json`. The `audits-*` commands read the separate `audits` collection, not this log, so nothing in the CLI reads the audit trail.
- `bin_alerts` writes to `floor.json` and `outbox` writes to `outbox.json`. Something outside this repo, such as the mailer daemon or a floor display, may read those files. Confirm before you change the file names or formats.

My static check flagged only `send_digest` and `_parse_legacy_asn` as uncalled helpers. Every other function in the 366 command modules is used within its own module.