**Call: HOLD on 002. Migration 001 can ship by itself.**

The plan's rollback line is wrong. It says both migrations are "schema changes, so this is safe and reversible like any other code change." Migration 002 is not reversible.

**Biggest risk:** `002_migrate_total_to_cents.sql` adds `total_cents`, backfills it, and runs `DROP COLUMN total` in one script, in the same deploy that switches `app.py` to read `total_cents`. After it runs, `git revert` brings back the old code, but the old code reads a `total` column that no longer exists. The old values are gone unless a backup exists, and the plan doesn't mention one.

**Rollback loses data at:** the `DROP COLUMN` in 002. What's lost is the original float `total` values. They could only be rebuilt from `total_cents / 100.0`, and any precision beyond cents is already gone. Anything written after the deploy would also have to be copied back by hand.

| Step | Forward | Backward | Lossy from here? |
|---|---|---|---|
| 001 add `notes` | `ADD COLUMN notes TEXT` | `DROP COLUMN notes` (nothing reads it yet) | No, but the drop would discard any notes written meanwhile |
| 002a add `total_cents` | `ADD COLUMN` | `DROP COLUMN total_cents` | No |
| 002b backfill | `UPDATE ... ROUND(total*100)`, unbatched | Re-run it, or null the column | No |
| 002c `DROP total` | Same script as 002a/b | None | **Yes, point of no return** |
| `app.py` read switch | Reads `total_cents` | Revert the commit | Only safe while `total` still exists |

**Blockers**
1. **Expand and contract are in one deploy.** The skill rules out "a single ALTER that both adds and removes on a live system" and dropping the old column in the same deploy that switches reads. Old app instances still running during a rolling deploy read `total` after it's dropped, so they break mid-deploy.
2. **No dual-write.** Orders written between the backfill and the app switch get `total_cents` NULL, because the old code only writes `total`.
3. **No data check or backup.** The tests use one row and don't cover NULLs or non-cent values. No backup or copy-based verification is cited. The `UPDATE` is also unbatched, so a large table means a long lock.
4. **No signals or limited rollout.** The plan names no watch signal and no canary or flag.
5. **Rollback is untested.** The plan names only a code revert, and I found no tested rollback for the data.

**What I ran:** `test_migration.py` passes (2 tests, *proven*). It only proves the forward path on one row, and one of its two tests asserts that `total` is gone, which is the dangerous behavior. It says nothing about rollback.

**Path to a go**
1. **Ship 001 now.** It's additive and reversible, with nothing reading `notes`. The plan doesn't name a watch signal for it, but any basic error-rate check is enough for this step.
2. **Deploy A (expand):** `ADD COLUMN total_cents`, with the app dual-writing `total` and `total_cents`.
3. **Backfill in batches.** Re-runnable, and run on a copy first. Check row counts, no NULLs and a sample of real values.
4. **Deploy B:** switch reads to `total_cents` behind a flag or canary. Watch the share of orders with NULL `total_cents` and the display-total error rate.
5. **Deploy C, later:** drop `total` only after a backup is taken and restore is tested. This is the point of no return, and it needs the owner's explicit sign-off.

Prepared but not run: I made no deploys or live data changes. I can write the expand migration, the batched backfill, the dual-write change and a tested backward script, if you want them.