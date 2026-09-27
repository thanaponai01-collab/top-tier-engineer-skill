No, it shouldn't go tonight as written. The tests pass, but I ran the migration on a copy of `data/prod.db` and it breaks two things. The real database is untouched.

**1. It deletes every phone number.** `003_contacts.sql` creates `contacts` but never copies anything into it, then drops `users.phone`. Prod has 3 users with phones (Ana, Bo, Cy). After migrating the copy, `contacts` was empty and the phone column was gone. There's no down-migration, so the only way back is a backup.

**2. The nightly reminder job crashes.** `jobs/reminders.py` still reads `SELECT name, phone FROM users`. Against the migrated copy it fails with `OperationalError: no such column: phone`. So tonight's reminder texts wouldn't go out at all.

The suite is green because it only covers `app/profile.py`, which already reads from `contacts`. Nothing tests the reminders job, and nothing migrates a database that already has phone data in it.

**What I'd change before shipping:**
- **Copy before dropping.** Add `INSERT INTO contacts (user_id, phone) SELECT id, phone FROM users WHERE phone IS NOT NULL;` to 003. Better still, move the `DROP COLUMN` into a later 004 migration. Then old code running between step 2 (migrate) and step 3 (restart) of `DEPLOY.md` doesn't break either.
- **Point `recipients()` at `contacts`:** join `users` to `contacts` on `user_id`.
- **Add two tests:** one for `recipients()`, and one that migrates a database already at version 2 with phones and checks they end up in `contacts`.
- **Back up `data/prod.db` before step 2.** `DEPLOY.md` doesn't include a backup step. Also, `migrate.py` uses `executescript`, which commits as it goes, so a failure partway through a migration isn't rolled back.

Want me to make those changes?