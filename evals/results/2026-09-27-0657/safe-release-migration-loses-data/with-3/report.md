**Hold. It can't go tonight as written.** Step 2 of `DEPLOY.md` would permanently delete every user's phone number, and the nightly reminders job would crash the first time it ran. There's no rollback. Once the migration runs, the phone data is gone unless you restore a backup.

I ran it against a **copy** of `data/prod.db` (`/tmp/copy.db`). I didn't touch prod.

| Finding | Evidence |
|---|---|
| **Phone data is deleted.** `003_contacts.sql` creates `contacts` and then runs `DROP COLUMN phone` without copying anything across first. | Proven. Before: 3 users, 3 with a phone. After: `contacts` has **0 rows** and `users.phone` is gone. |
| **Reminders job breaks.** `jobs/reminders.py:7` still reads `SELECT name, phone FROM users`. | Proven. On the migrated copy it raises `no such column: phone`. Step 3 restarts that job. |
| **The green suite doesn't cover either problem.** `test_profile.py` starts from an empty in-memory database, inserts straight into `contacts`, and never tests reminders. | Traced. The 2 tests pass (I ran them). |
| **The add and the drop are in one step.** The expand and contract happen in the same deploy, so this migration is also the point of no return. | Traced. |

**What goes wrong, and what's lost:** as soon as `migrate.py` runs 003, every user's phone number is lost. There are 3 in this copy of prod. SMS reminders then stop entirely. The only way back is restoring the database from a backup, and `DEPLOY.md` doesn't take one.

**A safe order.** Each deploy below needs its own yes:
1. **Expand (reversible).** Rewrite 003 to create `contacts` and backfill it: `INSERT OR IGNORE INTO contacts (user_id, phone) SELECT id, phone FROM users WHERE phone IS NOT NULL;`. Leave `users.phone` in place. Back up `prod.db` before running it.
2. **Switch reads (reversible).** Ship `profile.py` (already done) and `reminders.py` reading from `contacts JOIN users`. Add a test that migrates a database seeded with phones and checks both profile and reminders. Check on a copy that the counts match (3 → 3) and read the migrated rows. Then watch the reminder recipient count stay at 3 instead of dropping to 0.
3. **Contract (lossy, later).** In a separate deploy, add `004`, which drops `users.phone`. After this step, rollback means restoring the backup.

I didn't find any code that writes to `users.phone`, so dual-writing may not be needed. Check whatever creates or edits users outside this repo before step 3.

Should I make those changes (the split 003, the `reminders.py` update and the new test) and rerun it on a copy? Nothing will be run against `data/prod.db` without your go-ahead.