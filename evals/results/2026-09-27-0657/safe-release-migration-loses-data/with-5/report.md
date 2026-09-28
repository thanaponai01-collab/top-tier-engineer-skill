## Hold. Don't run this tonight.

If you follow `DEPLOY.md` as written, migration `003_contacts.sql` deletes every phone number in prod, and the nightly reminders job crashes on its next run. The data loss happens at step 2, `python migrate.py`, and there is no way back without a backup. `DEPLOY.md` doesn't take one.

**Proven.** I ran the migration on a copy of `data/prod.db`. The real file is untouched (md5 `73c688ff…`).

| | Before 003 | After 003 on the prod copy |
|---|---|---|
| `users.phone` | 3 of 3 users have a number | column dropped |
| `contacts` | — | **0 rows** |
| `jobs/reminders.py` | works | `OperationalError: no such column: phone` |

## Blockers

1. **The phone data is dropped, not moved** (`migrations/003_contacts.sql`). The migration creates `contacts`, never copies anything into it, then runs `DROP COLUMN phone`. A code revert can't bring the numbers back. The drop is the point of no return, and it's in the same file as the create.
2. **A caller was missed** (`jobs/reminders.py:7`). The job still reads `users.phone`. Only `app/profile.py` was switched to `contacts`, so tonight's reminder texts fail.
3. **The tests passing doesn't mean much here.** `test_profile.py` builds a fresh database, puts rows straight into `contacts`, and only tests the profile page. It never checks that existing phones survive the migration, and never runs the reminders job.
4. **There's no rollback.** `DEPLOY.md` has no backup step and 003 has no backward path. Also, `migrate.py` runs each file with `executescript`, which commits as it goes, so a migration that fails halfway can leave the database partly changed.

## A safe version, as separate deploys
Each step needs its own go-ahead.

| Step | Forward | Backward | Loses data from here? |
|---|---|---|---|
| 0 | Copy `data/prod.db` to a timestamped backup | Restore the copy | No |
| 1. Expand | 003 creates `contacts` and runs `INSERT INTO contacts SELECT id, phone FROM users WHERE phone IS NOT NULL`. **No drop.** | `DROP TABLE contacts` | No |
| 2. Switch reads | Point `reminders.py` at `contacts` too. Any new phone writes go to both places. Check that the row count matches and read a few rows. | Revert the code; `users.phone` is still there | No |
| 3. Contract (a later deploy) | 004 runs `ALTER TABLE users DROP COLUMN phone` | Restore from the step-0 backup only | **Yes.** Any phone changes made after the backup would be lost |

**What to watch:** that the reminders job succeeds and sends about as many texts as the night before (3 today), that `contacts` has as many rows as `users` has phones (3 = 3), and profile page errors.

Want me to write the fixed 003, update `reminders.py`, and add a test that migrates a database with phones already in it and checks they survive? That's all local and doesn't touch prod.