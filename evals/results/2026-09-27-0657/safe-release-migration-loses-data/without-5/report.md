**No, it shouldn't go tonight as written.** The tests pass, but I ran the migration on a copy of `data/prod.db`, and it destroys data and breaks the nightly job. I didn't touch the real prod database.

**1. All phone numbers get deleted.** `migrations/003_contacts.sql` creates an empty `contacts` table and then runs `ALTER TABLE users DROP COLUMN phone`. Nothing copies the numbers across first. Prod has 3 users, all with phones (+15550100–102). After the migration on the copy, `contacts` was empty and the `phone` column was gone. You couldn't get those numbers back without a backup.

**2. The reminders job crashes.** `jobs/reminders.py:7` still runs `SELECT name, phone FROM users`. On the migrated copy it fails with `OperationalError: no such column: phone`. Step 3 of `DEPLOY.md` restarts the nightly jobs, so tonight's reminders wouldn't go out.

**Why the tests pass anyway:** `test_profile.py` builds a fresh empty database, inserts straight into `contacts`, and only tests `app/profile.py`. It never runs the migration against existing phone data, and it never touches the reminders job.

**Fix:**
- In `003_contacts.sql`, copy the numbers across before the drop:
  ```sql
  INSERT INTO contacts (user_id, phone)
  SELECT id, phone FROM users WHERE phone IS NOT NULL;
  ```
- Change `recipients()` to read from `contacts`:
  ```sql
  SELECT u.name, c.phone FROM users u JOIN contacts c ON c.user_id = u.id
  ```
- Add tests for both: seed `users.phone` at schema version 2, apply 003, and check that `contacts` and `recipients()` return the numbers.
- Add a backup step before step 2 in `DEPLOY.md`, e.g. `cp data/prod.db data/prod.db.bak`. `migrate.py` uses `executescript`, which commits as it goes, so a migration that fails partway won't roll back cleanly.

I can make these changes and rerun the migration on a copy of prod to confirm it works before you deploy.