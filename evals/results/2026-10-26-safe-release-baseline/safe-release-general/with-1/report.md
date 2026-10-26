**My call: stage it, don't ship tonight on autopilot.** The migration and its rollback both checked out on a copy of the live DB. There are two blockers before `deploy.sh` will do what you expect:

1. **`deploy.sh` will not ship this.** It runs `git pull`, but `fixture/` isn't a git repo here and you asked me not to commit. As things stand, tonight's deploy would roll out whatever is upstream, not these changes. Someone has to commit and push them first, and tag the current release so the rollback in DEPLOY.md (`git checkout <previous tag>`) has something to point at.
2. **Biggest risk: callers I can't see.** `create_order` and `refund` now take integer cents and raise `TypeError` if passed a float, so a leftover dollar caller fails loudly instead of quietly storing 19.99¢. The only callers in this repo are the tests and the worker, but the web app's request handlers aren't here. Any handler still passing dollars will fail every order create or refund it handles. Someone needs to grep the real web code before 21:00.

**Does any rollback lose data?** No, not in this release. The old `total` column is kept and still written, so nothing becomes unrecoverable tonight. The point of no return is a later, separate deploy that drops `total`. Any old-code writes to `total` that never reached `total_cents` would be lost at that point, so that one needs its own sign-off.

**Rollout scope:** this is one box with one DB, so the change hits all traffic at once. There's no canary or flag. That makes the go decision yours.

## What changed (not committed)
- **`migrations/m0003_total_cents.py`** (new): adds a nullable `total_cents INTEGER` column next to `total` and fills it from `round(total*100)`. Re-running the fill is safe. Two triggers fill `total_cents` whenever old code writes only `total`, which covers the worker finishing its batch for up to 40 minutes after the restart, or a rolled-back release. `down` removes the triggers and the column.
- **`app/orders.py`**: all amounts and arithmetic are now integer cents. It writes both columns and reads only `total_cents`.
- **`worker/invoices.py`**: adds up cents instead of rounding floats. Its output format is unchanged.
- **`tests/test_orders.py`**: switched to cents, plus 4 new tests:
  - the ticket's bug (30¢ refunded as 3 × 10¢ must end at 0 / `refunded`)
  - floats are rejected
  - writes from old code keep `total_cents` correct
  - new code keeps `total` correct for old readers

| Step | Forward | Backward | Loses data? |
|---|---|---|---|
| m0003 (tonight) | add column, fill it, add triggers | `python migrate.py down 2` | No |
| Code switch (tonight) | read/write cents | deploy previous tag | No (triggers cover old writes) |
| Drop `total` (later, separate deploy) | — | — | **Yes**: point of no return |

## Evidence
- **Tests:** 8/8 pass. I broke the code twice on purpose to check the new tests catch real problems: turning off the triggers made the old-code-writes test fail, and dropping the `total` writes made the old-reader test fail.
- **The bug is real:** on the old code, a 30¢ order refunded as 10¢ + 10¢ + 10¢ rejects the third refund with "refund is more than the order".
- **Rehearsal on a copy of `data/shop.db`** (320 rows):
  - the migration applied cleanly and every row's `total_cents` matches `round(total*100)`
  - the 19 NULL totals are all drafts and stay NULL; no paid order has a NULL
  - spot checks look right: 34.089999… became 3409, 20.159999… became 2016
  - invoice output was byte-identical between old and new code for all 25 days
  - the old worker running against the new schema gave the same output
  - with old code against the new schema, an order of 7.77 refunded 0.77 got `total_cents` = 700, as it should
  - `down 2` left a full dump identical to the original
  - running `up` again after `down` worked
- **Live DB untouched:** its sha256 matches the copy I took before starting. Scratch files are in `work/`.

## How to back out
Run `git checkout <previous tag> && ./deploy.sh`. That's enough on its own: the extra column is harmless to old code, and the triggers keep it correct. I ran this path on the copy. If you also want the schema back at version 2, run `python migrate.py down 2` after the old worker has restarted. I also ran that on the copy, and it lost nothing.

## What to watch (none of this exists yet, so you'd be checking by hand)
1. **Errors in the shop-web logs**, especially `TypeError: amount must be integer cents`. Any at all means roll back.
2. **Drift between the two columns:** `SELECT count(*) FROM orders WHERE total IS NOT NULL AND total_cents IS NOT CAST(round(total*100) AS INTEGER);` should stay 0.
3. **The 23:00 invoice run:** compare its totals with the same day computed the old way. The worker restart should finish by about 21:40, well before the run.

Once the changes are committed and pushed, and the web handlers are confirmed to pass cents, I'd say it's fine to go at 21:00.