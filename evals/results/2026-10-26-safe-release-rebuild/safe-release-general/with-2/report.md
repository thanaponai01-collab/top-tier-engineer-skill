**It's safe to ship tonight at 21:00, with one catch: don't roll back the way DEPLOY.md says to.** The migration and both versions of the code were tested on a copy of `data/shop.db`. The live database wasn't written to, and nothing is committed.

## What changed (PAY-31)
- **`migrations/m0003_total_cents.py`**: adds a new `orders.total_cents INTEGER` column and fills it from `ROUND(total*100)`. The 19 draft orders with no total stay NULL. The old `total` column stays, and two triggers update `total_cents` whenever something writes only `total`. That covers the old worker, which keeps running against the new schema for up to 40 minutes while it finishes its batch, and old code after a revert.
- **`app/orders.py`**: amounts are now stored and refunded as whole cents. Callers still pass and get dollars, converted once using `Decimal`. A full refund of 34.09 now lands on exactly 0 and the order is marked `refunded`. It still writes `total` as well, for old code.
- **`worker/invoices.py`**: the invoice run adds up `total_cents` instead of floats.
- **`tests/test_orders.py`**: two new tests, one for cent-exact refunds and one for old-style writes keeping `total_cents` correct. All 6 tests pass.

## What the tests on the copy showed
- `python migrate.py up` succeeded, and running it a second time also succeeded. The new column was filled for all 320 rows.
- Three checks (reading every order, creating and refunding an order, and the invoice totals per day) passed on:
  - today's code with today's data
  - the new code on the migrated data
  - today's code on the migrated data, which covers both the 40-minute worker overlap and a code-only rollback
- `python migrate.py down 2` gave back every row unchanged. Today's code still worked afterwards.

## How to back out
**Code-only revert (recommended; no data lost):**
1. `git checkout <previous tag>`
2. `systemctl restart shop-web`
3. `systemctl restart shop-worker`

Don't use DEPLOY.md's `git checkout <tag> && ./deploy.sh`. Checking out a tag leaves git on a detached HEAD, and then `deploy.sh` stops at `git pull --ff-only` before it restarts anything.

**If you also want the schema undone:** run `python migrate.py down 2` *before* step 1, while the new migration file is still in the tree. This step is optional and was tested without losing data; the only change is that values like 34.089999999999996 come back as 34.09.

There's no point after which going back loses data, because both old and new code keep writing `total`.

## What to watch after 21:00
- This query should always return 0; anything else means roll back: `SELECT count(*) FROM orders WHERE total IS NOT NULL AND total_cents IS NOT CAST(ROUND(total*100) AS INTEGER)`
- Errors in shop-web or shop-worker that mention `total_cents`, or new refund errors.
- The 23:00 invoice run: totals per customer should match `SUM(total)` for that day. If they don't, roll back before invoices go out.

## Not covered by the tests
- the real `deploy.sh` run (git, systemd)
- live traffic hitting the database during the migration (it's 320 rows, so a very short lock)
- any other callers or services that read `orders` that aren't in this folder

Before you deploy, take a snapshot: `sqlite3 data/shop.db ".backup data/shop.db.pre-pay31"`.

I deleted the `.release/` working folder afterwards, since you asked me not to commit.