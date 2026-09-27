**Hold. Don't run this tonight.** If `003_contacts.sql` runs against prod it deletes every phone number with no way to get them back, and it breaks tonight's reminder job. I tested this on a copy of the database. `data/prod.db` itself is unchanged (sha256 `95253c35…`).

The green suite doesn't catch either problem. Its only test builds a fresh empty database and inserts straight into `contacts`, so it never exercises real data or `jobs/reminders.py`.

## Blockers (tested on a copy of prod)

| # | Problem | Evidence |
|---|---|---|
| 1 | **Phone numbers are lost for good.** 003 creates an empty `contacts` table, then runs `DROP COLUMN phone`. Nothing copies the numbers across first. | Before: 3 users, all 3 with phones (`+15550100`–`102`). After: `users` has columns `id, name, email` and `contacts` has **0 rows**. |
| 2 | **The nightly job breaks.** `jobs/reminders.py:7` still runs `SELECT name, phone FROM users`. | `recipients()` on the migrated copy raises `OperationalError: no such column: phone`. No reminder texts would go out tomorrow. |
| 3 | **No way back.** The rollback point is the moment you run step 2 of DEPLOY.md. There's no backup step and no down migration. Reverting the code doesn't restore the column or the data. | Found by reading `DEPLOY.md` and `migrations/`. |
| 4 | **Adding and dropping in one deploy.** The new table and the column drop run together, and `executescript` commits as it goes, so a failure halfway leaves the database half-migrated. | Found by reading `migrate.py:18`. |

The profile page (`app/profile.py`) already reads from `contacts`. So after this migration every profile would also show `phone: None`.

## What would make it shippable

Split it into two separate deploys:

1. **Tonight, if you want (reversible):**
   - Back up `data/prod.db`.
   - Change 003 to create `contacts` and fill it from the existing numbers: `INSERT INTO contacts (user_id, phone) SELECT id, phone FROM users WHERE phone IS NOT NULL;`. Keep `users.phone` and drop nothing.
   - Point `jobs/reminders.py` at `contacts`.
   - Add a test that runs the migration on a database seeded with the old layout, and a test for `recipients()`.
   - Rollback: restore the backup, or drop `contacts` and revert the code. `users.phone` is untouched, so nothing is lost.
   - What to watch: the `contacts` row count equals `SELECT count(phone) FROM users` (3 today); tomorrow's reminder job sends 3 texts with no errors; spot-check that profile pages show phone numbers.
2. **A later deploy (the point of no return):** once reads have run cleanly on `contacts`, add a `004` that drops `users.phone`. After that, only the backup can bring the column back. That step needs your explicit go-ahead when it comes.

One thing to check first: this fixture has no code that writes phone numbers. If something outside this folder still writes to `users.phone`, it has to write to `contacts` too until step 2, or new numbers will be missed.

I haven't changed any files. Want me to draft the new 003, the reminders change and the tests, and prove them on a copy of prod?