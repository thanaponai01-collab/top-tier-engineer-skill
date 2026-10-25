About 99% of the code is reachable. Nothing reaches seven pieces, and one of those is a bug rather than leftover code. I read every non-command file, checked the 360 generated command files against their 12 templates (all identical apart from the collection name), and ran the CLI against a throwaway data directory. Nothing in `fixture/` was changed.

## Reachable

The entry points are the two scripts in `pyproject.toml` and the nightly job the README describes:

- **`depot` (`depot/cli.py`)**: `registry.all_commands()` imports every module in `depot/commands/`, so anything with `@command` is live. `depot help` lists 364 commands:
  - 360 generated ones: 30 collections × 12 verbs (check, count, list, newest, oldest, search, show, stats, summary, tags, top, zones).
  - `bins-pick` and `inbound-receive`, which publish events on `bus` → `handlers/audit.py` (write to the audit log) and `handlers/bin_alerts.on_bin_low`.
  - `orders-ship`.
  - `export` (`report_export.py`), which loads the exporter named on the command line. That makes **csv, json and xml all reachable**, since a user can pass any of them.
  - Shared code they use: `store`, `settings` (`DATA_DIR`, `LOW_STOCK`), `registry`, `bus`.
- **`depot-admin` (`depot/admin.py`)**: `compact` and `reseed`.
- **`python -m depot.jobs`**: runs what `schedule.json` lists, which is `daily_digest` and `age_stock`. `daily_digest` calls `notify.build_digest`.

"Reachable" means an entry point can get to it. It doesn't mean anyone runs it. If you have shell history or wrapper logs, check which of the 360 generated commands are actually used. They're probably the biggest saving available, but the code can't tell you that.

## Built but nothing reaches it

| Piece | Why nothing reaches it | What I'd do |
|---|---|---|
| **`handlers/bin_alerts.on_bin_empty`** (subscribes to `"bin.emptied"`) | `bins_pick._state()` returns `"empty"`, so the event published is `bin.empty`. The names don't match. I emptied bin 1 in the scratch run: the audit log got its line, but no floor note was written. | **Port it, and fix the event name.** This is a bug, not dead code: the floor is meant to get "schedule a refill" notes and currently doesn't. Tell ops before migrating. |
| **`notify.send_digest` + `outbox.py`** | `daily_digest` calls `build_digest` and throws the result away. Nothing ever calls `send_digest`, so nothing goes to the outbox or the mailer daemon. The nightly digest only prints a count. | **Ask the floor leads whether they expect that email.** If they do, it's another bug: port both pieces and have the job call `send_digest`. If they don't, drop both, and drop `build_digest` too, since its output goes nowhere. |
| **`jobs/purge_audit.py`** | It exists, but `schedule.json` doesn't list it. Meanwhile the audit log grows on every pick and receive and is never trimmed. | **Port it and schedule it** (or use the new platform's log retention). Someone probably forgot to add it to the schedule. |
| **`commands/bins_rebalance.py`** | It has a full `run()` but no `@command`, so it isn't registered and `depot help` doesn't show it. | **Ask ops before porting.** It edits stock, so don't switch it on quietly. If nobody wants it, drop it. |
| **`crossdock.py` + `settings.CROSSDOCK_ENABLED = False`** | It's only imported inside `orders-ship` behind a flag that's hard-coded off. The comment says "pilot, waiting on the ops review". | **Hold it until the ops review decides.** Don't port it by default. If the pilot goes ahead, port it with the flag; if not, delete the module, the flag and the branch in `orders_ship.py`. |
| **`inbound_receive._parse_legacy_asn`** | Never called. Its docstring says the format is from before the EDI switch. | **Drop it.** Check first that no supplier still sends fixed-width ASNs. |
| **`depot/__main__.py`** (for `python -m depot`) | Doesn't exist, so that's not an entry point. | No action. Just don't assume it exists on the new platform. |

## Port-time notes
- Several modules reach into the "private" `store._path`: the audit handler, the bin-alerts handler, outbox and purge_audit. On the new platform, make it a public API.
- Commands are found by scanning the package directory with `pkgutil` at runtime. If the new platform bundles or zips the code, that scan may find nothing. Use an explicit list of commands instead.