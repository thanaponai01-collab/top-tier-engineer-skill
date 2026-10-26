**It's safe to ship at 21:00.** The `safe-release` gate passed (`RELEASE-GATE: done(ship, lossless way back)`). Nothing was committed, and `data/shop.db` was not touched: every rehearsal ran on copies of it.

## The change
- **`migrations/m0003_total_cents.py`** adds `orders.total_cents INTEGER` and fills it with `ROUND(total*100)`. The 19 draft orders with no total stay NULL. Two triggers fill `total_cents` whenever code that only knows `total` inserts or updates a row. This adds a column and leaves `total` in place, because `DEPLOY.md` says the old worker keeps running against the new schema for up to 40 minutes after the deploy.
- **`app/orders.py`** reads `total_cents` and does refund arithmetic in integer cents. Dollar amounts are converted with `Decimal`. It still writes `total` (cents / 100) so old code sees correct values. Function signatures are unchanged, so callers still pass dollars.
- **`worker/invoices.py`** adds up `total_cents` per customer and divides by 100 once.
- **`tests/test_orders.py`** has two new tests:
  - The PAY-31 case: refunding 0.10 then 0.20 from a 0.30 order. Today's code rejects the second refund because the float result goes below zero.
  - Rows written by old code still get a correct `total_cents`.

  All 6 tests pass.

## What the rehearsal showed
- The migration ran on a copy of the live data, and running it twice was harmless.
- **New code on migrated data:** the probe passed. It reads all 320 orders, runs invoices for every day, and creates and refunds an order.
- **Today's code on migrated data:** also passed. That covers the 40-minute worker window and a code-only revert.
- **Undo (`python migrate.py down 2`):** returned the data row for row to how it is today, and today's code passed again afterwards.
- My first probe refunded 19.99 then 9.99 and crashed on today's code. That's the PAY-31 bug happening in the live code path, so I switched the probe to amounts float handles exactly.

## How to back out
1. Run `git checkout <previous tag> && ./deploy.sh`. The migration step does nothing on the old code, and old code runs fine with the new column there.
2. This step is optional. Once both `shop-web` and `shop-worker` have finished restarting on the old code, run `python migrate.py down 2`. Don't run it while new code is still running: the new code reads `total_cents` and will fail without it.

**Point of no return:** none in this release, because `total` is kept up to date. You can't go back once a later migration drops `total`. That needs its own release after nothing reads it any more.

## What to watch
- **`shop-web` errors** mentioning `total_cents`, "no such column", or refund `ValueError`s. Any of these means roll back.
- **Mismatched rows.** This query must stay at 0:
  `SELECT COUNT(*) FROM orders WHERE total IS NOT NULL AND (total_cents IS NULL OR total_cents != CAST(ROUND(total*100) AS INTEGER))`
  Check it before the 23:00 invoice run.
- **The 23:00 invoice run.** A customer's total can now differ by 1 cent from what the old float sum would have given; that's the fix working. A bigger gap means roll back.

## Not covered by the rehearsal
- The real `deploy.sh` run: `git pull` and the `systemctl` restarts. This folder isn't a git repository, so the change needs to reach whatever checkout `deploy.sh` pulls from before 21:00.
- Live traffic during the restart.
- Any other service or script that reads `orders.total`. I only found the web app and the worker. Others would keep working, since `total` stays up to date.

I deleted the skill's working folder (`.release/`) and its probe script, since nothing is being committed.