**It's safe to ship tonight.** I tried the migration and the rollback on copies of `data/shop.db` with both the new code and the code running today. Both versions work on the migrated data, and the rollback gave back the data exactly as it was, so nothing is lost. The live database was only ever opened read-only and is still at schema version 2 with no new column. Nothing is committed.

## What changed
- **`migrations/m0003_total_cents.py` (new):** adds a `total_cents INTEGER` column and fills it from `total` for all 320 orders. It also adds two database triggers that update `total_cents` whenever old code writes only `total`. The `total` column stays and the two are kept in step. This is deliberate: during deploy the old worker keeps running for up to 40 minutes against the new schema, and it stays correct. Running the migration twice does no harm. Removing `total` is a separate migration once this has settled.
- **`app/orders.py`:** callers still pass dollars. Each amount is converted to whole cents once, and refunds are worked out in cents. It writes both `total_cents` and `total`, and the receipt line is formatted from cents.
- **`worker/invoices.py`:** adds up whole cents per customer instead of rounding float sums.
- **`tests/test_orders.py`:** two new tests, including the actual bug. A stored order of `34.089999999999996` used to fail a full refund of `34.09` with "refund is more than the order"; now it refunds fully. All 6 tests pass.

## How it was checked
- The migration and both versions of the code were run on copies of the live database.
- Old code writing new orders after the migration still keeps `total` and `total_cents` in agreement on every row.
- Rolling back after the migration returned the data row for row, and today's code still works afterwards.

## How to back out
- **Code only (enough on its own):** check out the previous release and restart `shop-web` and `shop-worker`. Today's code works on the migrated data. The extra column and triggers can stay.
- **Also removing the column:** run `python migrate.py down 2` *before* switching code, while the new migration file is still checked out. Then check out the previous release and restart both services.
- **Don't roll back with `./deploy.sh` from a checked-out old tag.** That is what `DEPLOY.md` says to do, but `git pull --ff-only` fails when you're not on a branch, and `set -e` stops the script there. Restart the services directly instead.
- No step loses data: rolling back only drops `total_cents` and the triggers, and `total` stays current on every write.

## What to watch after 21:00
1. This query should return 0. Anything higher means roll back:
   `SELECT count(*) FROM orders WHERE (total IS NULL) != (total_cents IS NULL) OR CAST(round(total*100) AS INTEGER) != total_cents`
2. `KeyError: total_cents` or "refund is more than the order" errors in the `shop-web` logs.
3. The 23:00 invoice run: totals should match each customer's sum of `total` for the day to the cent.

## Not covered
The real `deploy.sh` run (git and systemd on the server), live traffic, and any other program outside this repo that reads `orders`. Any such reader is unaffected, since `total` is unchanged. The rehearsal files in `.release/` have been deleted.