## Verdict: hold. Don't run it tonight as written.

Migration `003_contacts.sql` would permanently delete every user's phone number, and it would break the nightly reminders job. Green tests don't catch either problem, because the tests start from an empty database and don't cover `jobs/`.

I proved both by running `migrate.py` on a copy of `data/prod.db`. The real prod db was opened read-only and is unchanged.

| # | Problem | Evidence |
|---|---|---|
| 1 | **Phone numbers are lost.** `003` creates `contacts` but never copies phones into it, then drops `users.phone` in the same step. There's no backfill and no way back. | Prod has 3 users, all 3 with phones (e.g. Ana `+15550100`). After the migration on the copy: `contacts` has **0 rows** and `users` has no `phone` column. |
| 2 | **The reminders job crashes.** `jobs/reminders.py:7` still reads `SELECT name, phone FROM users`. Step 3 of `DEPLOY.md` restarts it. | On the migrated copy, `recipients()` fails with `OperationalError: no such column: phone`. No reminder texts go out. |
| 3 | **There's no rollback.** `DEPLOY.md` has no backup step and `migrate.py` has no down path. | Once `DROP COLUMN` runs, the phones are gone unless someone copied the file first. |

The profile page (`app/profile.py`) already reads from `contacts`. So even without the drop, every profile would show no phone until a backfill runs.

## What would make it shippable

Split `003` into two deploys:

**Tonight: add and copy only (reversible).** Replace `003_contacts.sql` with:
```sql
CREATE TABLE contacts (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    phone TEXT NOT NULL
);
INSERT OR IGNORE INTO contacts (user_id, phone)
    SELECT id, phone FROM users WHERE phone IS NOT NULL;
```
and switch `jobs/reminders.py` to `SELECT u.name, c.phone FROM users u JOIN contacts c ON c.user_id = u.id`. Also add a test for `recipients()`.

- **Rollback:** restore the pre-deploy copy of `prod.db`, or `DROP TABLE contacts` and revert the code. Either way no data is lost, because `users.phone` is still there.
- Add a step 0 to `DEPLOY.md`: `cp data/prod.db data/prod.db.pre-003`.
- **What to watch:** the `contacts` row count should equal the number of users with a phone (3 now). Also watch whether the reminders job ends up with the same number of recipients as before (3), and whether profiles still show phones.

**Later, as a separate `004`: drop the old column.** Run `ALTER TABLE users DROP COLUMN phone;` only after the job and profile pages have been running on `contacts`. Also confirm first that nothing writes phones into `users.phone` any more. **This is the point where rollback starts losing data:** any phone written to `users.phone` after the backfill would be lost. I only checked the repo, and nothing in it writes phones. If some outside process does, `004` needs a second backfill before the drop.

I haven't edited any files or touched prod. Should I make the tonight changes (new `003`, the reminders fix and its test, the backup step in `DEPLOY.md`) and re-run them against a fresh copy of prod? Running the actual deploy would still be your call.