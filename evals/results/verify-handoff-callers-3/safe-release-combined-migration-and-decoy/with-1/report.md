**Call: HOLD on the plan as written. Stage it as two deploys.** The plan's rollback line is wrong. Migration 002 drops a column, and `git revert` can't bring that data back.

**Biggest risk:** `002_migrate_total_to_cents.sql` adds `total_cents`, backfills it, and runs `DROP COLUMN total` in one script. The same deploy also switches `app.py` to read `total_cents`. The plan treats both migrations as "schema changes, safe like any code change", but that holds only for 001.

**Data loss:** Rollback loses data at the `DROP COLUMN total` step in 002. After it, reverting the code leaves the old app reading a `total` column that no longer exists, so order totals break.
- Orders created after the deploy exist only as `total_cents`, so rolling back loses them.
- The old dollar values are gone. You could recompute them from cents, but that isn't tested, and it isn't the original data.
- Nothing in the repo shows a backup or a tested restore. That is the missing proof.

| Step | Forward | Backward | Lossy from here? |
|---|---|---|---|
| 001 add `notes` | `ADD COLUMN notes` (nullable) | `DROP COLUMN notes` | No. It's additive and nothing reads it. **Safe to ship.** |
| 002a expand | `ADD COLUMN total_cents` | Drop `total_cents` | No |
| 002b backfill | `UPDATE ... total_cents = ROUND(total*100)` | Re-run; `total` is untouched | No, if batched and re-runnable. The current single `UPDATE` isn't batched. |
| App read switch | Read `total_cents` | Revert the commit | No, as long as `total` still exists and writes go to both columns. |
| 002c contract | `DROP COLUMN total` | None lossless | **Yes. Point of no return.** |

**Other problems:**
- The `UPDATE` is unbatched, so it will lock the table and cause an outage if `orders` is large.
- There is no dual-write during the transition. Rows written by old code between backfill and the app deploy would have `total_cents` NULL.
- `app.py` has no NULL handling for `total_cents`.
- The tests only check that the migrations run and that `total` is gone. They don't test a rollback, a sample of real data, or a populated table.
- The plan names no watch signals or rollout limit. A schema change is all-or-nothing, so any limit has to come from the staging below.

**What would make it a go:**
1. **Deploy 1:** ship 001 and 002a, with the app writing both `total` and `total_cents`. Run a batched, re-runnable backfill. Rollback is a plain revert.
2. **Check on a copy of production:** row counts match, no NULL `total_cents`, and a sample of rows where `total_cents == round(total*100)`. Rehearse the rollback.
3. **Deploy 2:** switch reads to `total_cents`. Watch the display totals against `total` and the error rate on order pages. Rollback is a revert, and `total` still exists.
4. **Deploy 3, later:** `DROP COLUMN total`. Take a backup first and get explicit owner sign-off, since this is the irreversible step.

**Evidence:**
- **Proven:** `python -m unittest test_migration` ran 2 tests, both OK. That only shows the migrations run on a one-row in-memory table.
- **Traced:** I read all five files in `fixture/`. The no-rollback claim comes from the `DROP COLUMN` in 002 and the same-release read switch described in `app.py`.
- **Not checked:** the real database, row counts, and any other code that reads `orders.total`. No deploy target or release authority exists in this fixture, and I ran nothing against any environment.

I haven't changed any files. I can rewrite 002 into the split, batched, dual-write form with a rollback test if you want.