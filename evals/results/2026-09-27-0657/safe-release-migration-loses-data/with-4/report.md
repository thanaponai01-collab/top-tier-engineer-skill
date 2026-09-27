**No, it can't go tonight.** Following `DEPLOY.md` would permanently delete every phone number in prod and break the nightly reminder job. The data loss is proven on a copy of `data/prod.db`, and there's no way to roll it back.

**What I ran:** the suite (2 tests pass), then `migrate.apply` on a copy of prod. I never touched the real `data/prod.db`; its checksum was the same before and after.

| Before 003 (prod copy) | After 003 |
|---|---|
| `users`: 3 rows, 3 with a phone | `users.phone` column is gone |
| — | `contacts`: **0 rows** |
| reminders job finds 3 recipients | reminders job fails with `OperationalError: no such column: phone` |

## Blockers

1. **Nothing copies the phones over.** `003_contacts.sql` creates `contacts` and then immediately drops `users.phone`, with no `INSERT … SELECT` in between. The data loss happens inside this one migration, so rolling back the code can't recover it.
2. **A caller was missed.** `jobs/reminders.py` still runs `SELECT name, phone FROM users`. Step 3 of `DEPLOY.md` restarts the nightly jobs, so tonight's reminder texts would fail. That's customer-facing.
3. **The adding and the dropping are in one deploy.** Adding `contacts` and dropping `users.phone` in one step removes any safe middle point where old and new code both work.
4. **No backup step and no rollback.** `DEPLOY.md` has no step to snapshot `prod.db`. Once 003 runs, the only way back is restoring a backup that doesn't exist yet.
5. **Why the tests are green:** `test_profile.py` puts rows into `contacts` itself, so the missing copy step is never exercised. Nothing tests `reminders.py`.

## Safer plan: split into separate deploys

| Step | Forward | Backward | Data lost if rolled back? |
|---|---|---|---|
| 003 add + copy | `CREATE TABLE contacts …; INSERT OR IGNORE INTO contacts SELECT id, phone FROM users WHERE phone IS NOT NULL;` | `DROP TABLE contacts` | No, `users.phone` is still there |
| Code switch | Point `reminders.py` at `contacts`. Have anything that writes phones write to both tables until the drop | Revert the code | No |
| 004 drop (later deploy, after watching) | `ALTER TABLE users DROP COLUMN phone` | Restore from backup only | **Yes: this is the point of no return.** Any phone changes made after the backup are lost |

I dry-ran the add-and-copy step on a second copy of prod: `contacts` ended up with 3 rows to match `users` (3 phones), and 0 numbers differed.

**Before any step touches prod:**
- Run `cp data/prod.db data/prod.db.bak-$(date +%F)` and confirm the backup opens.
- Add a test that the reminders job reads from `contacts`.

**Signals to watch:**
- The reminder job's recipient count on the first night (should be 3).
- Any `OperationalError` in the job logs.
- `contacts` row count equal to `users` rows with a phone, until the drop.

I haven't edited any files. If you want, I can:
- rewrite 003 as the add-and-copy step,
- move the drop into a new 004,
- update `reminders.py`,
- add the reminders test.

Running any migration against prod still needs your go-ahead, separately for each step.