# Release call — migration 003

**Call: hold.** Shipping this tonight deletes every phone number in production and breaks the
nightly reminder job. The green suite can't see either problem.

1. **Data loss.** `003_contacts.sql` creates `contacts` and then drops `users.phone` in the same
   script, with no `INSERT INTO contacts SELECT ...` in between. Nothing copies the numbers across.
   Production has 3 users with phones. After 003 there are 0 and the column is gone, and there's no
   backward path. The point of no return is the `DROP COLUMN`, and what's lost is every phone number.
2. **A caller still reads the old column.** `jobs/reminders.py` does
   `SELECT name, phone FROM users`. After 003 it fails with `no such column: phone`. Only
   `app/profile.py` was moved to `contacts`.
3. **Why green doesn't mean ready.** `test_profile.py` migrates an empty in-memory database and
   inserts into `contacts` itself, so it never sees existing data or the job.

**Safe shape (expand, then contract):**
- Release A: create `contacts`, copy `users.phone` into it (safe to re-run), write both. Move
  `reminders.py` to `contacts`.
- Verify on a copy of `prod.db`: 3 rows in, 3 rows out, and read a sample.
- Release B, later and separately: drop `users.phone`.

I did not run `migrate.py` against `data/prod.db`. I only tried it on a copy.
