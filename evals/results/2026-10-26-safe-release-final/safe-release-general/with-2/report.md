**It's safe to ship tonight, and backing out loses no data.** I rehearsed both the release and the rollback on copies of `data/shop.db`. The live database was never written: it's still at schema version 2 with no new column. Nothing is committed.

## What changed
- **`migrations/m0003_total_cents.py`** (new) adds an integer `orders.total_cents` column and fills it with `ROUND(total*100)` for all 320 orders. The 19 draft orders with no total stay empty. Two triggers fill `total_cents` whenever old code writes only `total`.
- **`app/orders.py`** reads and writes cents. It still takes and returns dollars, converting with exact decimal rounding, so whatever calls it doesn't need to change. It also keeps writing `total` alongside.
- **`worker/invoices.py`** adds up whole cents instead of floats.
- **`tests/test_orders.py`** has two new tests that reproduce PAY-31: a 0.30 order refunded 0.10 then 0.20, and an order stored as 34.0899999… refunded 34.09. Both fail on today's code and pass on the new code; all 6 tests pass.

## Why it's safe during the deploy
`deploy.sh` runs the migration and only then restarts the web app (a few seconds) and the worker (up to 40 minutes). During that gap the old code is running on the new schema. So I added a column rather than converting `total` in place; converting it would have made the old worker read cents as dollars and invoice 100× too much. In the rehearsal:
- Today's code passed the read and write checks on the migrated data.
- When old code wrote orders and refunds, the triggers converted them correctly (29.999999… became 3000), and the new code then refunded them to exactly zero. Every row's `total` and `total_cents` still matched afterwards.
- Running the migration twice is harmless.

## How to back out
1. **Code revert (enough on its own, loses nothing):** `git checkout <previous tag> && ./deploy.sh`. The old `migrate.py` ignores version 3, and the old code keeps using `total`, which is still correct.
2. **Schema undo (optional):** only after both `shop-web` and `shop-worker` are back on the old code, run `python migrate.py down 2` from a checkout that still has `m0003_total_cents.py`. The old tag doesn't have it. This drops `total_cents`, and the rehearsal got every row back exactly as it was.

There's no point after which going back loses data.

## What to watch
- **Web logs:** any `no such column: total_cents` means roll back at once. "Refund is more than the order" errors should stop.
- **Drift check:** this should stay 0; anything else means roll back:
  `SELECT COUNT(*) FROM orders WHERE total_cents IS NOT CAST(ROUND(total*100) AS INTEGER)`
- **23:00 invoice run:** per-customer totals should match the day's `SUM(total)` rounded to cents. If any are off by 100× or by a cent, hold the invoices and roll back.

## Not covered by the rehearsal
- The real deploy, live traffic, and server config.
- Anything outside this repo that writes to `orders` (the triggers handle writers that only set `total`).
- This folder isn't a git repo, so `deploy.sh`'s `git pull` only picks the change up once you've committed and pushed it.