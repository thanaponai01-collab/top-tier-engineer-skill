# Wire-check: ledger (whole-system mode)

**The main finding is a live bug, not dead code.** `ledger checkout` builds a customer receipt and then throws it away. `commands/checkout.py:14` calls `receipt.build(order)` when it should call `receipt.send(order)`. Because of that, nothing is ever written to `outbox.jsonl` and the mailer daemon never gets a receipt. I proved this: after a checkout, `data/` contained only `orders.json`.

Everything below was run in a scratch copy with its own data directory. The fixture itself was not modified.

## Ways in (counted before tracing)

| Entry | Instances | Evidence |
|---|---|---|
| CLI `ledger` (`pyproject` → `cli:main`) | `add`, `list`, `checkout`, `export` | proven, ran each one |
| CLI `ledger-admin` (`admin:main`) | `reset`, `reindex` | proven (`reindex`); `reset` traced |
| Host cron → `python -m jobs.runner` → `jobs/schedule.json` | `nightly_backup`, `purge_exports` | proven, ran the runner; produced `orders.bak.json` and deleted `export-old.csv` |
| Plugins via the `LEDGER_PLUGINS` env var (dynamic import) | `sheets_sync`, `slack_hook` | proven *when enabled*. Whether any deployment enables them is **UNKNOWN** |
| External reader: the mailer daemon reads `outbox.jsonl` | 1 | **UNKNOWN**, not in this repo |
| External: whether the host crontab actually has the runner line | 1 | **UNKNOWN**, the docstring is the only evidence |

## What it actually serves

These are served: the four ledger commands, the two admin commands, `store.db`, the two scheduled jobs, and both plugins (but only when the env var turns them on). That is the whole of the README's stated purpose: take orders, check out, export.

## Inventory minus served = not reached

The inventory came from every `def` in the source, not from the walk.

| Piece | Status | First broken link | What I'd do |
|---|---|---|---|
| `notify.receipt.send` → `store.outbox.enqueue` | orphaned, **effect lost** (proven) | 5. Reachable: checkout calls `build()` and drops the return value | **Fix it, don't drop it.** A one-word change: `receipt.build(order)` → `receipt.send(order)` in `checkout.py:14`. Carry it into the orders/checkout service along with the outbox. First confirm with whoever runs the mailer daemon that it is still alive. If the daemon is gone, delete `notify/` and `store/outbox.py` together. |
| `jobs/compact_outbox.py` | orphaned | 2. Registered: not listed in `schedule.json` | Keep it, tied to the receipt fix. Once receipts start flowing, `outbox.jsonl` grows forever without this job. Register it in `schedule.json` at the same time as the fix. It only drops lines marked `"sent": true`, so check that the daemon actually sets that flag. If the receipt path is dropped, delete this job too. |
| `pricing/coupons.py` | orphaned | 4. Invoked: guarded by `settings.COUPONS_ENABLED = False` ("pricing review pending, see #212"). Proven: `checkout 1 SPRING10` charged 100.00 | **The owner decides, not the code.** Ask what happened to #212. If coupons are coming, move it into the pricing/checkout service still behind the flag. If not, delete it along with the flag and the branch in checkout. Don't carry it over by default. |
| `reports/weekly.py` | orphaned | 2. Registered: no command, no job, no import anywhere | Ask who uses the "Monday meeting" summary. Someone may run it by hand with `python -c`, which nothing in the repo can show. If someone uses it, add it as a `ledger report` command or a scheduled job in a reporting service. If nobody claims it, delete it. |

Unknowns are counted separately. That's two plugins, which depend on deployment config, plus the existence of the cron entry and of the mailer daemon. So the served set above is not complete until someone checks each deployment's `LEDGER_PLUGINS` value and the host crontab.

## Served, but worth knowing before the split

- **`purge_exports`** deletes `export-*.csv` from whatever directory cron runs in. `ledger export` writes wherever the user tells it to. Those two only meet by convention, so the job may clean up nothing, or the wrong files. Before it moves to its own service, give it an explicit path.
- **`nightly_backup` and the whole store** default to the relative path `data/`, so they also depend on cron's working directory unless `LEDGER_DATA` is set. Splitting into services makes this shared-file assumption a real cross-service contract.
- **`ledger-admin reindex`** renumbers order IDs. Any service that stores an order ID will break after a reindex.

## The repair (not applied, as you asked)

```python
# commands/checkout.py:14
    receipt.send(order)
```
```json
// jobs/schedule.json — add:
  {"job": "compact_outbox", "cron": "0 4 * * *"}
```

## Recommendation

Add a smoke check that runs `ledger add x 1 && ledger checkout 1` against a temporary `LEDGER_DATA` and asserts that `outbox.jsonl` gains a line. Add a second check that fails if any module in `jobs/` other than `runner` is missing from `schedule.json`. Those two checks would have caught the two non-flag gaps here, and they should carry over into the split services.