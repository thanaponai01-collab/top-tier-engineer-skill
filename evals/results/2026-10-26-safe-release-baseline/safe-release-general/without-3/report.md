I've made the change, and it's safe to ship tonight once you've done the two checks below. I tested on copies of `data/shop.db`; the live file is unchanged (same checksum before and after). Nothing is committed.

## Why I didn't just convert the column
`DEPLOY.md` says the **old worker keeps running against the new schema for up to 40 minutes** after the migration. If `total` were converted to cents in place, the old worker would read 1999 as $1999.00 and print invoices 100× too big. Old code would also break on a rollback. So this release only **adds** a cents column and keeps the old dollars column correct:

- **`migrations/m0003_total_cents.py`** adds `orders.total_cents INTEGER` and fills it from `total`. It also adds two triggers: if old code writes only `total` (the old web app in the seconds before it restarts, or after a rollback), `total_cents` is filled in automatically. `down()` removes the triggers and the column.
- **`app/orders.py`**: amounts are now integer cents. It reads `total_cents` and writes both columns. Passing a float raises `TypeError`, so a caller still sending dollars fails loudly instead of storing a value 100× too small.
- **`worker/invoices.py`** adds up cents exactly, and prints the same `12.50` format as before.
- **Tests**: I converted the existing ones to cents and added tests for exact partial refunds, rejecting floats, old code still seeing correct dollars, old-code writes filling in cents, and the migration's up/down. All 9 pass.

## Results on a copy of the live DB
- The migration took about 0.1s. All 320 rows match `round(total*100)` exactly.
- The 19 rows with no total are all drafts, and they get no cents value either (expected).
- All 183 existing per-customer daily invoices come out identical under the old and new code.
- `migrate.py down 2` returns the schema exactly to what it is now.

## Before 21:00
1. **Commit and push this yourself.** `deploy.sh` starts with `git pull`, and I haven't committed (the fixture isn't even a git repo here). Without that, the deploy ships nothing new.
2. **Check that no other code calls `create_order` or `refund`.** Their amounts changed from dollars to cents. There are no other callers in `fixture/`, but anything outside it that still sends floats will now get a `TypeError`.

## Backing out
- **Normal rollback, code only:** `git checkout <previous tag> && ./deploy.sh`, as `DEPLOY.md` describes. Leave the migration in place. The old code ignores `total_cents`, `total` stays correct the whole time, and the triggers keep `total_cents` filled in if you deploy forward again. The `migrate.py up` step inside `deploy.sh` does nothing on the old code.
- **Removing the schema change too (optional):** after rolling back the code, run `python migrate.py down 2`. Tested on a copy, it's quick. Copy `data/shop.db` first anyway.
- Avoid deploying during the 23:00 invoice run, as usual.

## Follow-up ticket
In a later release, once nothing reads `total` any more, drop `total` and the two triggers. That's when the dollar floats are actually gone; until then they're kept only so old code and rollbacks keep working.