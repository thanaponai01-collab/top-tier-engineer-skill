I'd **stage it, not ship it blind.** The change is ready and was rehearsed on a copy of `data/shop.db`, and backing out doesn't lose data. But I couldn't test the git side of the deploy or rollback, and there's no monitoring for this, so whether to go at 21:00 is your call. If you do, watch the checks listed below.

**Biggest risk:** this is all-or-nothing. There's one box, no flag and no canary, so every order is on the new code as soon as `shop-web` restarts.

**Does any rollback lose data?** No, not with this release. The old `total` column stays and is kept in sync both ways. The point where a rollback would lose data comes later, when a separate deploy drops `total`. At that point the dollar amounts the old code needs are gone.

**One trap in the rollback.** Run `python migrate.py down 2` *before* you check out the old code. If you check out the old tag first, `down 2` can't find the new migration file, does nothing and reports no error. I tested this: it left the database at version 3. That isn't harmful, because old code works fine on the new schema, but it means the schema wasn't rolled back.

## What changed (uncommitted, in `fixture/`)
- **`migrations/m0003_total_cents.py`** (new): adds a `total_cents INTEGER` column next to `total` and fills it with `round(total*100)`. It also adds two database triggers. When old code writes only `total`, the triggers set `total_cents` to match. That covers the few seconds while `shop-web` restarts, the old worker's batch of up to 40 minutes, and any time after a rollback. It's safe to run twice. Undoing it drops the triggers and the column.
- **`app/orders.py`**: all the arithmetic is now in integer cents. Callers still pass and receive dollars, so nothing else has to change. Every write updates both `total_cents` and `total`.
- **`worker/invoices.py`**: adds up cents instead of rounding floats.
- **`tests/test_orders.py`**: four new tests. They cover the cent bug, writes from old code, `total` staying correct for a rollback, and migration down then up.

There are no config changes, new secrets or dependency changes. The only extra thing this release carries is migration 0003.

## Migration steps
| Step | Forward | Backward | Loses data? |
|---|---|---|---|
| Add column and triggers (0003) | `migrate.py up` | `migrate.py down 2` | No |
| Fill `total_cents` | Inside 0003. 320 rows, one statement | Column dropped | No, `total` is unchanged |
| Read from cents | New code | Old code, which reads `total` | No, both columns are written |
| Drop `total` | **Not in this release.** Do it later, separately | n/a | **Yes**, the old code's dollar values are gone |

## Evidence
- **Tests:** all 8 pass. Three of the new tests fail or error when run against the old code, so they do check the fix.
- **The bug is in live data.** Order #2 is stored as `34.089999999999996`. The old code rejects a full $34.09 refund with "refund is more than the order"; the new code refunds it to 0 and marks it `refunded`.
- **Copy of the live database:**
  - All 320 rows are still there and none disagree between the two columns.
  - The 19 empty totals are all drafts.
  - The total in cents, 663726, matches the old total.
- **Invoices:** for every day from Oct 1 to Oct 25, the old and new code produce exactly the same output. The old worker also runs fine on the new schema.
- **Rollback, code only:** old code creating orders and refunding on the new schema left no mismatch. Rolling forward again also worked.
- **Rollback, full:** after `down 2` the order data was byte-identical to before the migration, and the table and its triggers were back to how they were.
- **Live database untouched:** `data/shop.db` has the same SHA-256 as before (`4bf144…7867`).

**Not tested:**
- **Git steps:** the `git pull` / `git checkout <tag>` steps. `fixture/` isn't a git repo, and `deploy.sh` deploys whatever is on the remote. Since I didn't commit, **these changes won't go out until someone commits and pushes them.**
- **Service restarts:** the `systemctl` restarts.

## Before 21:00
Take a backup with `sqlite3 data/shop.db ".backup data/shop-pre-PAY31.db"`. Only use it as a last resort: restoring it loses any orders placed after the backup.

## Rollback (one sentence)
Run `python migrate.py down 2` while the new code is still checked out, then `git checkout <previous tag> && ./deploy.sh`. I tested the database part of this on copies. I couldn't test the git part.

The faster option is to skip `down 2` and just check out the old code and redeploy. The old code works on the new schema, and the triggers keep `total_cents` correct.

## What to watch (none of this exists yet, so run it by hand)
1. **Mismatches between the columns, which should always be 0.** Check right after deploying, at about 21:45 once the worker has restarted, and after the 23:00 invoice run:
   `python -c "import sqlite3;print(sqlite3.connect('data/shop.db').execute('select count(*) from orders where total is not null and (total_cents is null or total_cents != cast(round(total*100) as integer))').fetchone())"`
   **Roll back if it's above 0.**
2. **Errors from refunds**, especially "refund is more than the order", in the `shop-web` logs. If these go up rather than down, roll back.
3. **The 23:00 invoice run.** Compare its totals with `sum(total)` for that day. Any difference larger than a cent means roll back.

My rehearsal copies of the database are in `scratch/` next to `fixture/`. Delete them whenever you like.