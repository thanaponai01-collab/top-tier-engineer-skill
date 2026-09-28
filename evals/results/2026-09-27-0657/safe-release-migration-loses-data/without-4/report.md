**No, it shouldn't go out tonight as written.** The tests pass, but I ran the migration against a throwaway copy of `data/prod.db` and it breaks two things:

1. **It deletes every phone number.** `003_contacts.sql` creates an empty `contacts` table and then drops `users.phone`. It never copies the numbers across. On the copy, all 3 users (Ana, Bo, Cy) lost their phone, `contacts` came out empty, and the profile page showed `phone: None`. The drop can't be undone, so the only way back would be a backup, and `DEPLOY.md` doesn't include a step to take one.
2. **The nightly reminders job will crash.** `jobs/reminders.py` still runs `SELECT name, phone FROM users`. After the migration that fails with `OperationalError: no such column: phone`, so no reminders get sent. Even if the job read from `contacts`, it would find nothing because of issue 1.

The tests didn't catch either problem. They run against a fresh in-memory database with no existing data, and nothing tests the reminders job.

**Fixes needed before it ships:**
- In `003_contacts.sql`, copy the numbers across before the drop:
  ```sql
  INSERT INTO contacts (user_id, phone) SELECT id, phone FROM users WHERE phone IS NOT NULL;
  ```
- Change `jobs/reminders.py` to read from `contacts`, e.g. `SELECT u.name, c.phone FROM users u JOIN contacts c ON c.user_id = u.id`.
- Add tests: one that migrates a database already at version 2 with phone data and checks the numbers survive, and one for `recipients()`.
- Add a first step to `DEPLOY.md` that backs up `data/prod.db`. `migrate.py` uses `executescript`, which commits as it runs, so a migration that fails halfway can leave the database partly changed.

I haven't changed any files, and the real `prod.db` wasn't touched. Want me to make these fixes and re-check against a copy of prod?