**No, it shouldn't go out tonight as written.** The tests pass, but I ran the migration on a copy of `data/prod.db` and it causes two problems. The real prod DB was not touched.

**1. It deletes every user's phone number.** `migrations/003_contacts.sql` creates an empty `contacts` table and then runs `ALTER TABLE users DROP COLUMN phone`. Nothing copies the numbers across first. Prod has 3 users with phones (`+15550100`–`+15550102`). After migrating the copy, `contacts` was empty and the phone column was gone, so the numbers were lost with no way back except a backup.

**2. The nightly reminders job will crash.** `jobs/reminders.py` still runs `SELECT name, phone FROM users`. On the migrated copy it fails with `OperationalError: no such column: phone`. Step 3 of `DEPLOY.md` restarts that job, so tonight's reminders would not be sent.

**Why the suite is green:** the only test file is `test_profile.py`. It builds a fresh empty database and adds contacts directly, so it never checks that existing phones get moved, and nothing tests the reminders job.

**Fix before shipping:**
- In `003_contacts.sql`, copy the data before the drop:
  ```sql
  INSERT INTO contacts (user_id, phone) SELECT id, phone FROM users WHERE phone IS NOT NULL;
  ```
- Change `jobs/reminders.py` to read from `contacts` (join on `users` for the name).
- Add tests that run 001–002, insert a user with a phone, apply 003, and check both the profile page and `recipients()`.
- Back up `prod.db` before running step 2. `migrate.py` runs each file with `executescript`, which commits as it goes, so a failure partway through can leave the schema half-changed and not recorded in `schema_version`.

I can make these changes and re-run the migration on a copy of prod to confirm the numbers survive. Want me to?