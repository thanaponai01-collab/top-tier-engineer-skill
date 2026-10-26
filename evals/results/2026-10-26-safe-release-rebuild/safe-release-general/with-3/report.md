**Yes, it's safe to ship tonight, with one condition.** Any code outside `fixture/` that calls `create_order` or `refund` must pass cents. Inside `fixture/` there are no such callers. I rehearsed the migration, the deploy window and both ways back on copies of `data/shop.db`. All passed, and going back loses no data. The live database hasn't been touched: it's still at version 2 with no new column.

## What changed
- **`migrations/m0003_total_cents.py`** adds `orders.total_cents INTEGER` and fills it from `round(total*100)`. The 19 draft orders have no total, so they stay empty. The old `total` column stays. Two triggers fill `total_cents` whenever old code writes only `total`.
- **`app/orders.py`** now works in integer cents: `create_order(customer, total_cents)` and `refund(order_id, amount_cents)`. A float amount raises `TypeError` instead of being stored as the wrong number. It writes both `total_cents` and `total`.
- **`worker/invoices.py`** adds up whole cents. The printed invoice format is unchanged.
- **Tests:** updated to cents, plus new tests for exact partial refunds (the PAY-31 bug), rejecting dollar amounts, and the triggers. All 7 pass.

**Why the old column stays:** your deploy restarts the worker last, and the old worker can run on the new schema for up to 40 minutes. A plain revert would also put old code on the new schema. Old code ran cleanly on the migrated data in the rehearsal, and the two columns stayed in agreement.

## How we'd back out
1. **Normal rollback:** `git checkout <previous tag> && ./deploy.sh`, exactly as `DEPLOY.md` says. This was rehearsed. The new column stays but does no harm, and the triggers keep it up to date, so you can re-deploy the fix later unchanged.
2. **Optional, to remove the column too:** do this while the new code is still checked out. Stop `shop-web` and `shop-worker`, run `python migrate.py down 2`, then do step 1. It has to come first because the old checkout doesn't have the m0003 file. This was also rehearsed: the data came back identical to today's.

There's no point after which going back loses data.

## What to watch after 21:00
- Any `TypeError: amounts are integer cents` in the `shop-web` logs means something is still passing dollars. Roll back.
- This query should stay at 0: `SELECT count(*) FROM orders WHERE CAST(round(total*100) AS INTEGER) IS NOT total_cents`
- Spot-check the 23:00 invoice run for one day against the database.

## Before you deploy
- **The change won't ship as things stand.** `deploy.sh` does a `git pull`, and per your instruction nothing is committed (`fixture/` isn't a git repo here). Someone has to commit and push it first.
- **Not covered by the rehearsal:** the real `systemctl` restarts, live traffic, and any callers that aren't in `fixture/`.

I deleted the `.release/` working files when I finished.