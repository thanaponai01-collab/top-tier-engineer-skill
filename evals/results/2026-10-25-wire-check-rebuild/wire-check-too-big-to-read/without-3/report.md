## Summary

Nearly everything is reachable. Six pieces are not: one is a live bug, and the other five are dead or dormant code. I didn't change any files. The only thing I ran was `bins-pick` and `bins-rebalance`, against a throwaway `$DEPOT_DATA` directory, to confirm two of the findings.

## How code gets reached

There are three entry points:
1. **`depot`** (`depot/cli.py`), set in `pyproject.toml`. `registry.all_commands()` imports every module in `depot/commands/`, and a command exists only if it has `@command(...)`. It also imports `depot.handlers`, which subscribes the event handlers.
2. **`depot-admin`** (`depot/admin.py`) has a fixed list of tools: `compact` and `reseed`.
3. **`python -m depot.jobs`** runs only the jobs named in `depot/jobs/schedule.json`, which are `daily_digest` and `age_stock`. The host's cron calls it nightly.

Because commands and jobs are loaded by name at runtime, a plain "who imports this?" search gives the wrong answer. I traced the registry, the schedule file, the event bus and the exporter lookup by hand.

## Reachable (port these)

- **364 registered CLI commands:**
  - 30 record types (audits, bins, … zones), each with the same 12 commands: check, count, list, newest, oldest, search, show, stats, summary, tags, top, zones.
  - 4 special commands: `bins-pick`, `inbound-receive`, `orders-ship`, and `export` (that last one lives in `report_export.py`, so the file name doesn't match the command name).
  
  I checked all of them: every one has `@command`, no names are duplicated, and every private helper is called.
- **`export`'s three formats:** `exporters.get(fmt)` imports `csv_export`, `json_export` or `xml_export` by name, so all three are live even though nothing imports them directly.
- **Events:** `stock.moved` (sent by pick and receive) goes to `handlers/audit.py`. `bin.low` goes to `bin_alerts.on_bin_low`.
- **Admin tools:** `compact` and `reseed`.
- **Nightly jobs:** `daily_digest` and `age_stock`.
- **Shared code:** `store`, `settings`, `bus`, `registry`, and `notify.build_digest`.

## Built but nothing reaches it

| # | Piece | Why it's unreached | What I'd do |
|---|---|---|---|
| 1 | `handlers/bin_alerts.py: on_bin_emptied` | **This is a bug.** `bins_pick._state()` returns `"empty"`, so the event sent is `bin.empty`, but the handler listens for `bin.emptied`. I confirmed it: picking bin 1 down to 0 wrote "low" to `floor.json` but never "empty: schedule a refill". | **Port it and fix the event name** (one name or the other). The floor isn't getting refill notices today. Confirm with ops which name is intended. |
| 2 | `notify.send_digest` and all of `outbox.py` | `daily_digest` calls `build_digest()` and throws the result away. Nothing calls `send_digest`, so nothing is ever written to the outbox and the mailer daemon never gets a digest. | **Ask the owners before deciding.** The job looks like it was meant to call `send_digest`. If floor leads expect a daily email, fix it to call `send_digest` and port the outbox. If nobody has missed it, drop `send_digest`, `outbox.py`, and the digest-building in the job. |
| 3 | `jobs/purge_audit.py` | Not listed in `schedule.json`, so cron never runs it. Meanwhile `audit.json` gets a line appended on every pick and receive, so it grows without limit. | **Port it and schedule it**, or use the new platform's log retention instead. Either way, the audit log needs a size cap. |
| 4 | `commands/bins_rebalance.py` | Fully written, but it has no `@command`. Running `depot bins-rebalance` gives "unknown command". | **Ask ops whether they want it.** If yes, register it and test it, because it has never run in production. If no, drop it. Don't port it as dead code. |
| 5 | `crossdock.py` (and the branch in `orders_ship.py`) | It's wired in but turned off: `settings.CROSSDOCK_ENABLED = False`, and the comment says it's "waiting on the ops review". | **Leave it out of the initial port** and keep it in history. If the ops review approves it, port it then. It's 10 lines. If you'd rather keep it now, port it behind the same flag. |
| 6 | `inbound_receive._parse_legacy_asn` | Never called. Its docstring says the format is from "before the EDI switch". | **Drop it.** It's leftover code from an old supplier format. |

## Other things to check during the move

These aren't unreachable code, but they're in the live paths:
- `depot-admin compact` deletes every row with `qty <= 0`, so it removes empty bins from `bins`, not just from orders. That may not be what's intended.
- Commands publish events only because `cli.py` imports `depot.handlers` for its side effects. If the new platform's entry point skips that import, auditing and floor alerts stop silently.