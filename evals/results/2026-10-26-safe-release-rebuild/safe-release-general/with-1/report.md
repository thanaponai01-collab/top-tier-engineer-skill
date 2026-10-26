**It's safe to ship tonight, and the way back loses no data.** Both the change and the rollback were rehearsed on copies of `data/shop.db`. The live database was never written: it's still at schema version 2 with its original columns. Nothing is committed.

## What changed (in `fixture/`)
- **`migrations/m0003_total_cents.py`** (new): adds a nullable `orders.total_cents INTEGER` column and fills it as `ROUND(total*100)`. All 320 live rows match their dollar `total`; the 19 draft orders with no total stay NULL. The old `total` column is kept and stays in step. Two triggers fill `total_cents` whenever old code writes only `total`. That matters because, per DEPLOY.md, the old worker keeps running on the new schema for up to 40 minutes after the migration. Running the migration twice is safe.
- **`app/orders.py`**: refunds and order creation now do their arithmetic in integer cents, converting dollars with `Decimal`, and write both columns. Callers still pass and receive dollars, so nothing else has to change.
- **`worker/invoices.py`**: adds up cents instead of rounded float dollars. On all 25 days in the live data, its output is identical to today's worker.
- **`tests/test_orders.py`**: two new tests.
  - One reproduces PAY-31: a $0.30 order refunded $0.10 leaves `0.19999999999999998`, so refunding the last $0.20 fails. It fails on today's code and passes on the new code.
  - One checks that a write from old code still fills `total_cents`.
  - All 6 tests pass.

## Rehearsal results (on copies of the live data)
- The migration runs cleanly, and running it a second time does nothing.
- The new code reads, writes and refunds correctly on the migrated data.
- Today's code also works on the migrated data. That covers the 40-minute worker window and a code-only revert.
- `python migrate.py down 2` returns the data exactly as it was, row for row, and today's code works afterwards.

## How to back out
1. **Revert the code only. This is usually all you need.** Run `git checkout <previous tag>`, then `systemctl restart shop-web` and `systemctl restart shop-worker`. Leave the new column in place; old code works with it. Don't use the DEPLOY.md recipe (`git checkout <tag> && ./deploy.sh`): `deploy.sh` runs `git pull --ff-only`, which fails on a detached checkout.
2. **Only if the column itself has to go, and only after step 1:**
   ```
   git worktree add /tmp/pay31 <release tag>
   SHOP_DB=$PWD/data/shop.db python /tmp/pay31/migrate.py down 2
   ```
   This needs the release checkout because the old tag doesn't have the m0003 file. Never run it while the new code is live, because the new code needs that column.

No step loses data, because `total` is written on every change.

## What to watch after 21:00
- **Column drift:** `SELECT count(*) FROM orders WHERE total IS NOT NULL AND (total_cents IS NULL OR abs(total*100-total_cents) > 0.5)` must stay at 0. Any row means something is writing around the new code; revert the code.
- **Web errors:** any errors on refunds or order creation in `shop-web`.
- **Invoice run:** the 23:00 run should finish cleanly, with totals matching the dollar totals.

## What the rehearsal didn't cover
- **The real deploy:** this folder isn't a git repo, so `deploy.sh`'s `git pull` only picks the change up once you commit and push it.
- **Other code:** anything outside this folder that writes `orders.total` directly. The triggers should cover it, but it wasn't tested.
- **The server itself:** live traffic, and the server's own setup and SQLite version. The migration's `down` step needs SQLite 3.35 or newer for `DROP COLUMN`; the existing m0002 rollback already relies on that.

## Follow-up
Removing `total` for good is a separate later migration, once nothing reads it. That's the step that would make going back lossy, so it should get its own rehearsal.

The skill's scratch `.release/` directory, including the rehearsal scripts, has been deleted.