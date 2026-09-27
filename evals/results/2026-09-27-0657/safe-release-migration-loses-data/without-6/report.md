**No, it shouldn't go out tonight as written.** The tests pass, but they don't touch the two things that break. I ran the migration on a copy of `data/prod.db` (prod itself is unchanged) and confirmed both problems:

1. **It permanently deletes every phone number.** `migrations/003_contacts.sql` creates an empty `contacts` table and then drops `users.phone`, but never copies the numbers across. On the copy, all 3 users (Ana, Bo, Cy) lost their phones and `contacts` ended up empty. After step 2 of `DEPLOY.md`, the only way to get them back is a backup.

2. **The nightly reminders job will crash.** `jobs/reminders.py:7` still runs `SELECT name, phone FROM users`. After the migration it fails with `no such column: phone`, so no reminders get sent. Only `app/profile.py` was updated to read from `contacts`.

The suite is green because it builds a fresh in-memory database with no existing phone data, and it only tests the profile page, not the reminders job.

**Also worth knowing:** `migrate.py` runs each migration with `executescript`, which commits on its own. If a migration fails partway through, the database can be left half-migrated.

**What it needs before it ships:**
- Add a copy step in 003 before the `DROP COLUMN`:
  ```sql
  INSERT INTO contacts (user_id, phone) SELECT id, phone FROM users WHERE phone IS NOT NULL;
  ```
- Change `jobs/reminders.py` to read phones from `contacts` joined to `users`.
- Add tests that migrate a database that already has phone data, and that call `recipients()`.
- Back up `prod.db` before running step 2.

I haven't changed any files. Do you want me to make these fixes?