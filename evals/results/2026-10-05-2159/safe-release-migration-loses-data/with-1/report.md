**Hold. Don't release tonight.** I ran migration 003 on a copy of `data/prod.db`. I didn't touch the real file.

- **Data loss:** `003_contacts.sql` creates `contacts` but never copies phones into it, then drops `users.phone`. Prod has 3 users with 3 phones. After the migration on the copy, `contacts` had 0 rows. All 3 numbers were gone, and the profile page would show no phone for anyone. A `git revert` can't bring them back, and `DEPLOY.md` has no backup step.
- **Reminders job breaks:** `jobs/reminders.py` still runs `SELECT name, phone FROM users`. On the migrated copy it failed with `no such column: phone`. The nightly reminders would crash after deploy.
- **Green suite:** the tests cover only the profile page. The test database starts empty and inserts into `contacts` by hand, so a missing backfill can't show up. Nothing tests the reminders job.
- **Rollback:** none exists. The migration has no backward path, and I found no backup of `prod.db`. Once `phone` is dropped, the only way back is a restore from a backup that doesn't exist yet.

**What would make it ship-able** (the split follows the skill's expand → backfill → contract order):

1. **Deploy 1, expand and backfill:** the migration only creates `contacts` and runs `INSERT INTO contacts SELECT id, phone FROM users WHERE phone IS NOT NULL`. It leaves `users.phone` in place and is safe to re-run.
2. **Fix the reminders job:** read from `contacts`, and add a test for it.
3. **Check on a copy:** the contact row count should match the number of non-null phones (3 here), and a sample of rows should show the right numbers.
4. **Backup:** take a copy of `prod.db` before the prod run, and restore it on a copy once to prove the rollback works.
5. **Deploy 2, contract, later:** drop `users.phone` in a separate deploy, after the reads have been switched and watched.

**Watch signals:** the contact count against the non-null phone count, errors from the reminders job, and the share of profiles that show a phone.

I haven't changed any files or run anything against prod. I can write the backfill migration, the reminders fix and a test for it, and a backup-and-restore step for `DEPLOY.md`. Shall I do that?