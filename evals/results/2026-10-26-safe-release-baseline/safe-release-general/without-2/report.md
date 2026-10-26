## Verdict: safe to ship tonight, with two conditions

1. **The change has to be committed and pushed before 21:00.** `deploy.sh` begins with `git pull`, and `fixture/` isn't a git repo here. You told me not to commit, so I haven't, which means none of this goes out until you commit and push it.
2. **Check the callers I couldn't see.** `create_order` and `refund` now take integer cents, and passing a float raises `TypeError`. The fixture has no web handlers. If some caller outside `fixture/` still passes dollars like `19.99`, that call will fail. I made it fail on purpose so it can't quietly create a $0.20 order. Search the web layer for those two calls before deploying.

I'd also back up the database just before you run the deploy, because `deploy.sh` doesn't:
`sqlite3 data/shop.db ".backup data/shop-pre-PAY-31.db"`

## What changed
- **`migrations/m0003_total_cents.py`**: adds a `total_cents INTEGER` column and fills it with `ROUND(total*100)` for existing orders. The 19 draft orders with no total stay NULL rather than becoming 0. It also adds two triggers that keep `total_cents` in step whenever anything writes the old float `total` column. The old `total` column is still there.
- **`app/orders.py`**: all the money arithmetic now uses integer cents. It still writes `total` as cents/100 so older code keeps reading correct values.
- **`worker/invoices.py`**: adds up cents. The printed output format is unchanged.
- **Tests**: updated to cents, plus new tests for:
  - the PAY-31 bug itself (refunding 30¢ as 10¢ then 20¢ used to leave a tiny float remainder, so the order never reached "refunded")
  - floats being rejected
  - triggers keeping cents correct when old code writes
  - migrating down and back up

## Why the migration only adds and never removes
- **The deploy window:** `DEPLOY.md` says the old worker keeps running against the new schema for up to 40 minutes. It reads `total`, which is still there and still correct. The worker will have restarted by about 21:40, well before the 23:00 invoice run.
- **Rollback:** `git checkout <tag> && ./deploy.sh` only ever migrates up, so the schema change can't be undone through that path. Because the change only adds a column, it doesn't need undoing.

## Checks
- **Tests:** all 9 pass.
- **Rehearsal on a copy of `data/shop.db`:**
  - all 320 rows migrated
  - every `total_cents` matches `total`
  - old and new invoice code give identical totals on all 25 days
  - migrating down and back up works cleanly

  The live database is untouched and still at schema version 2.

## Backing out
- **Code problem:** `git checkout <previous tag> && ./deploy.sh`, as usual. The old code ignores `total_cents`, and the triggers keep it correct while the old code runs, so you can deploy forward again later without a manual fix.
- **Do not** run `migrate.py down 2` as part of a rollback. It isn't needed, and once you're back on this release the code requires the `total_cents` column.
- **Last resort:** restore the `.backup` file with both services stopped. Any orders placed since the backup would be lost.

**Follow-up for a later release:** once nothing reads `total` any more, drop that column and the two triggers.