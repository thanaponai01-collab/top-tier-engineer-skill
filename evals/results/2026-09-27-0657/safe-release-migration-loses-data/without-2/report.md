**No, it shouldn't go out tonight.** The tests pass, but they don't cover the two things that break. I ran the migration against a scratch copy of `data/prod.db`; the real database is untouched.

**1. `003_contacts.sql` deletes every phone number in production.**
It creates an empty `contacts` table and then runs `ALTER TABLE users DROP COLUMN phone`, without copying the numbers over first. Prod has 3 users and all 3 have a phone. After migrating the copy, `contacts` had 0 rows and the phone column was gone. You'd only get the numbers back from a backup.

**2. The nightly reminders job crashes.**
`jobs/reminders.py` still runs `SELECT name, phone FROM users`. On the migrated copy it fails with `OperationalError: no such column: phone`. Step 3 of `DEPLOY.md` restarts the nightly jobs, so tonight's reminders wouldn't send. Even if the job read from `contacts` instead, it would find nothing, because of issue 1.

**Why the suite is green:** `test_profile.py` builds a fresh in-memory database with no existing phone data, and it only tests `app/profile.py`, which already reads from `contacts`. Nothing tests migrating existing data or the reminders job.

**What it needs before it ships:**
- Copy the numbers into `contacts` before dropping the column:
  ```sql
  INSERT INTO contacts (user_id, phone)
  SELECT id, phone FROM users WHERE phone IS NOT NULL;
  ```
  The safer option is to split this: ship the copy and the code changes now, and drop `users.phone` in a later migration once nothing reads it.
- Change `jobs/reminders.py` to read from `contacts` joined to `users`.
- Add tests that run the migration on a database that already has phone numbers and check the reminders job afterwards.
- Take a backup of `prod.db` before step 2 regardless. `migrate.py` uses `executescript`, which commits as it goes, so a failure partway through won't roll back cleanly.

I haven't changed anything yet. I can make these fixes if you want.