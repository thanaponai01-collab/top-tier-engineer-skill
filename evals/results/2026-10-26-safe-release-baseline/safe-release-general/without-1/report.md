I've moved order amounts to integer cents and tested it. I think it's safe to ship tonight, with two things to sort out first (below). Nothing is committed, and I didn't touch `data/shop.db`. All the testing ran on throwaway copies, and I checked byte-for-byte afterwards that the live file is unchanged.

## What changed

- **`migrations/m0003_total_cents.py`** adds a `total_cents INTEGER` column and fills it from the existing `total` values. It deliberately keeps the old float `total` column. Per `DEPLOY.md`, the old worker keeps running against the new schema for up to 40 minutes, and a rollback runs old code. Both only know `total`, so renaming or dropping it tonight would break invoices.
- **Two triggers** keep `total_cents` correct whenever old code writes only `total`. That happens in the few seconds before `shop-web` restarts, and after any rollback.
- **`app/orders.py`** now does all its arithmetic in cents and writes both columns. Callers still pass and get back dollars, so the web app's calls don't change. Amounts are converted exactly (19.99 becomes 1999).
- **`worker/invoices.py`** adds up cents instead of rounding floats.
- **Tests:** 6 new ones. One reproduces the ticket: refunding 0.10 and then 0.20 from a 0.30 order. With float dollars the remainder is about -0.00000000000000003, so the second refund was rejected as more than the order. The others cover old code writing only `total`, the old column staying filled, draft orders with no total, and undoing then reapplying the migration. All 10 tests pass.

## Rehearsal on a copy of the live database

- 320 orders. All 301 non-null totals convert to whole cents with nothing lost. The 19 draft orders have no total, and theirs stay empty rather than becoming 0.
- After the migration, `total` and `total_cents` agree on every row.
- I ran the old and new invoice calculations for all 25 days in the data and they match exactly.
- Undoing the migration (`migrate.py down 2`) returns the table to its exact original schema.

## Before 21:00

1. **This code isn't in git.** `fixture/` isn't a git repository, and `deploy.sh` begins with `git pull`. The change only ships once you commit and push it the usual way; otherwise it either deploys the old code or stops at the pull.
2. **Back up the database first.** `deploy.sh` doesn't do it. For example: `sqlite3 data/shop.db ".backup data/shop.db.pre-pay31"`
3. **One behaviour change:** an amount with fractions of a cent (like a refund of 0.005) now raises `ValueError` instead of being stored as-is. I can't see the web app's handlers, so check that nothing passes amounts like that.

## How to back out

- **Normal rollback:** `git checkout <previous tag> && ./deploy.sh`, as documented. The migration step does nothing, the old code ignores `total_cents`, and the old `total` column has stayed correct the whole time, so no data needs fixing. The triggers keep `total_cents` correct during the rollback, so deploying forward again later is also safe.
- **Removing the column too (optional):** `python migrate.py down 2`, but only after the rollback is complete. Running it while the new code is live breaks the app, because the new code reads `total_cents`.
- **Last resort:** stop both services and restore the backup from step 2. Any orders taken since the deploy would be lost.

**Follow-up:** once nothing old can still be running, a later migration should drop `total` and the two triggers. That deploy needs the same care about the old worker's 40-minute overlap.