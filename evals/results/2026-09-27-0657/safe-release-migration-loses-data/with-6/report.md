**Hold. It can't go tonight as written.** Migration `003_contacts.sql` would permanently delete every phone number in prod and crash the nightly reminders job. There is no rollback: once the column is dropped, the data is gone. I ran it on a copy of `data/prod.db`, not on prod.

## What I ran (proven)

| Check | Result |
|---|---|
| `python -m unittest` | 2/2 pass |
| Prod before (read-only) | schema at version 2, 3 users, **3 have phones** |
| `migrate.apply` on a copy of prod | `contacts` has **0 rows**; `users.phone` is dropped |
| `jobs/reminders.recipients` on the migrated copy | `OperationalError: no such column: phone` |

## Blockers

1. **The data is never copied.** `003` creates `contacts` and drops `users.phone`, but nothing moves the phone numbers across. All 3 are lost the moment it runs. Adding and dropping in the same migration means there's no safe point to stop.
2. **One reader was missed.** `jobs/reminders.py:7` still reads `users.phone`. `DEPLOY.md` step 3 restarts the nightly jobs, so tonight's reminder texts would fail.
3. **The profile page goes silently wrong.** `app/profile.py` reads from `contacts`, which would be empty, so every user shows no phone. No error is raised.
4. **The tests can't catch any of this.** They start from an empty DB and insert straight into `contacts`. They never run the migration against existing data and never test the job.
5. **There's no backup or rollback step.** `DEPLOY.md` goes straight to `migrate.py data/prod.db` with no copy taken first. Also, `executescript` commits as it goes, so a migration that fails halfway leaves the database half-migrated.

## Safe path: three separate deploys

| Step | Forward | Backward | Loses data? |
|---|---|---|---|
| 0 | `cp data/prod.db data/prod.db.bak-<date>` | restore the file | no |
| 1. Expand (`003`) | `CREATE TABLE contacts …; INSERT OR IGNORE INTO contacts SELECT id, phone FROM users WHERE phone IS NOT NULL;` | `DROP TABLE contacts` | no |
| 2. Switch readers | change `reminders.py` to read `contacts`; write new phones to both places; ship with `profile.py` | revert the code | no |
| 3. Contract (`004`, a later deploy) | `ALTER TABLE users DROP COLUMN phone` | restore from backup only | **yes. From here on, rolling back loses any phones written after the backup.** |

Before step 1, run the new `003` on a copy and confirm the row counts match: `count(phone)` in `users` should equal `count(*)` in `contacts` (3 = 3). Also read those rows to check the values. Add a test that migrates a DB already at version 2 and has phone data, and a test for `recipients()`.

**What to watch after each step:** errors from the reminders job, the number of reminders sent compared with before, and how many profiles show a null phone.

If you'd like, I can write the split migrations, the reminders change and the new tests, and verify them against a prod copy. Running anything against `data/prod.db` still needs your yes for each step.