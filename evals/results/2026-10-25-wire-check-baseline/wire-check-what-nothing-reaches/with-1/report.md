I ran every entry point in a scratch copy with its own data directory, so nothing in `fixture/` changed.

**The main problem: checkout never sends customer receipts.** `commands/checkout.py:14` calls `receipt.build(order)`, which builds the message and throws it away. `receipt.send()` is the function that writes it to the outbox, and nothing calls it. I checked by running `ledger checkout 1`: afterwards the data directory had only `orders.json` and no `outbox.jsonl`. The mailer daemon has never been given anything to send. This is a live bug, not unused code.

## What the codebase serves

There are three ways in, all proven by running them:

| Way in | Declared in | What it serves |
|---|---|---|
| `ledger` command | `pyproject.toml` → `cli:main` | `add`, `list`, `checkout`, `export`. These use `store/db.py` and `settings.py`. |
| `ledger-admin` command | `pyproject.toml` → `admin:main` | `reset`, `reindex` |
| Host cron runs `python -m jobs.runner` | `jobs/schedule.json` | `nightly_backup`, `purge_exports` |

Two more ways in exist that I can't see from the code, so I count them as **unknown**, not unused:
- **Plugins** turned on by the `LEDGER_PLUGINS` environment variable in each deployment. `sheets_sync` adds a `sync-sheet` command, and `slack_hook` wraps `checkout`. Both work when the variable is set (proven). Whether any real deployment sets it isn't in the repo.
- **The mailer daemon** is outside this repo. Its only link to this code is the `outbox.jsonl` file.

## What nothing reaches

| Piece | Status | Where the chain breaks | What I'd do |
|---|---|---|---|
| `notify/receipt.send` + `store/outbox.py` | Not reached (proven) | **The result is thrown away.** Checkout calls `build` instead of `send`. | **Fix before the split.** Change `receipt.build(order)` to `receipt.send(order)` in checkout. Carry both files into the orders/notifications service. The fix is below. |
| `jobs/compact_outbox.py` | Not reached (traced) | **Not registered.** It's missing from `schedule.json`, so the runner never loads it. | Keep it, but tie it to the receipt fix. Once receipts start flowing, the outbox grows forever without it. Add `{"job": "compact_outbox", ...}` to the schedule when `send` is wired. Right now it would have nothing to compact. |
| `pricing/coupons.py` | Not reached (proven) | **Never runs.** It only runs when `settings.COUPONS_ENABLED` is true, and it's `False` pending #212. When I turned the flag on, VIP25 took 100.00 down to 75.00, so the code works. | **This is the owner's call, not dead code.** Ask whoever owns #212 whether pricing is happening. If yes, carry it over behind the flag. If no, delete it and the branch in checkout. Also note: `ledger checkout 1 VIP25` currently ignores the code without saying so, and the README advertises `[coupon]`. |
| `reports/weekly.py` | Not reached (traced) | **Not registered.** No import, no command, no schedule entry. Its docstring says "Monday meeting". | The only real candidate for deletion, but ask first. Someone may run it by hand with `python -c`. If it's wanted, register it as a CLI command or a cron job in the reporting service. If nobody claims it, drop it. |
| `integrations/sheets_sync`, `slack_hook` | Unknown | Turned on by the environment, outside the repo | Check the deployment configs for `LEDGER_PLUGINS` before deciding. Note that `sheets_sync` is a stub: it just prints "synced" and does no real work. If any deployment enables it, someone believes a sync is happening when it isn't. |

One caveat on a job that *is* reached: `purge_exports` only deletes files named `export-*.csv` in whatever folder cron runs from. I confirmed it deleted `export-old.csv` and left `out2.csv` alone. `ledger export` writes to whatever filename you give it, so the purge only works if people follow that naming habit. Either make it a convention or have the job read a configured folder.

## Fix for the main problem (not applied)

```python
# commands/checkout.py, line 14
-    receipt.build(order)
+    receipt.send(order)
```

Then schedule `compact_outbox` in `jobs/schedule.json`.

## How to stop this from happening again

Add one end-to-end check: run `ledger checkout` against a temporary data directory, then assert that `outbox.jsonl` contains a receipt for that order. It fails today and would pass after the fix. During the split, also add a check that every module under `jobs/` either appears in `schedule.json` or is explicitly excluded, so jobs that were written but never scheduled can't slip through.