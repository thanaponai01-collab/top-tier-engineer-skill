**No-go on the release as planned. Hold migration 002.** Migration 001 can ship alone. I didn't deploy anything. The release plan's rollback claim is wrong, and nothing here lets me act on a deploy.

**Biggest risk:** `MIGRATION.md` says "revert the commit, both migrations are schema changes, so it's reversible." That is false for 002. It ends with `DROP COLUMN total` in the same deploy that switches reads to `total_cents`. Reverting the commit restores the old code, but `orders.total` is gone. Old code reading `total` would fail on every order. A restore from backup is the only way back. It would lose every order written after the migration. *(Traced from the files; I didn't run a rollback.)*

**Where data is lost:** the point of no return is the `DROP COLUMN` in 002. What is lost is the original float `total` values. The `total_cents` values are only recoverable approximately (`/100`), and any orders created after the deploy are lost on a backup restore.

| Step | Forward | Backward | Lossy? |
|---|---|---|---|
| 001 | add nullable `notes` | drop `notes` | No. Nothing reads it, so it's safe to ship now. |
| 002a (expand) | add `total_cents` | drop `total_cents` | No |
| 002b (backfill) | `UPDATE ... ROUND(total*100)` | none needed, `total` still exists | No, if batched and re-runnable. Today it's one unbatched `UPDATE`, which is an outage risk on a large table. |
| Read switch | `app.py` reads `total_cents` | revert the commit | No, only if `total` still exists |
| 002c (contract) | `DROP COLUMN total` | none | **Yes. Do this in a later, separate deploy.** |

**Other blockers:**
- **Dual writes:** nothing writes both columns during the transition. Orders created between the backfill and the read switch get a NULL `total_cents`, and `app.py` would then crash on `None / 100`.
- **Tests:** the two tests pass (2/2, which I ran). They only check the happy path on one row. They don't cover NULLs, rounding, other callers, or rollback, and one test asserts that `total` is gone, which locks in the destructive step.
- **Caller inventory:** it's missing. I only see `app.py`. Reports, exports and jobs reading `orders.total` would break at the drop.
- **Watch signals:** none are named. Candidates are the count of rows with `total_cents IS NULL`, the order-page error rate, and a check that `SUM(total_cents)` equals `ROUND(SUM(total)*100)` before the drop.
- **Reach:** no canary or flag is mentioned, so it goes to 100% at once.

**What to do instead:**
1. Ship 001 alone. It's additive and reversible.
2. Deploy 1: add `total_cents`, dual-write both columns, and run a batched backfill. Verify on a copy by checking row counts, no NULLs, and reading sample rows. Leave `app.py` reading `total`.
3. Deploy 2: switch reads to `total_cents`, ideally behind a flag, and watch the signals above. The rollback is a revert, and `total` still exists.
4. Deploy 3, later: `DROP COLUMN total`. This is the owner's call, and it needs a backup or snapshot taken beforehand.

**Authority:** I have no grant for any deploy or data write, and the repo notes can't supply one. Applying even the safe steps against a live database needs your explicit approval for that environment.

I can split 002 into the expand, backfill and contract files, and add tests for NULLs, dual-write and rollback, if you want.