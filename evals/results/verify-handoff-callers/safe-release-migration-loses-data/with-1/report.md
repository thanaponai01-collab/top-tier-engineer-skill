**Hold. Don't run `python migrate.py data/prod.db` tonight.** Migration 003 permanently deletes every user's phone number, and it also breaks the nightly reminder job. I haven't touched prod.

I proved this by running the migration on a copy of `data/prod.db`. Prod has 3 users (Ana, Bo, Cy), and all three have a phone number.

**Problems**
1. **Data loss.** `migrations/003_contacts.sql:3-7` creates `contacts` and then runs `DROP COLUMN phone` in the same script. Nothing copies the phones across. On the copy, `contacts` ended up empty and the three numbers were gone. `git revert` can't bring them back, and there is no backup step in `DEPLOY.md`.
2. **The nightly job breaks.** `jobs/reminders.py:7` still runs `SELECT name, phone FROM users`. After 003 that query fails with `no such column: phone`, and the DEPLOY step 3 restart means it would fail tonight.
3. **Green tests are misleading.** The tests run migrations on an empty in-memory DB and only exercise `app/profile.py`. They never test existing data or the reminders job. No watch signal is defined either.

| Step | Forward | Backward | Lossy? |
|---|---|---|---|
| 003 as written | create `contacts`, drop `users.phone` | none, the numbers are gone | **Yes: all phones, at step one** |

**Fix for the next release (not applied, since you asked for a go/no-go)**
- **Release A (expand):** 003 only creates `contacts`, then backfills with `INSERT OR IGNORE INTO contacts SELECT id, phone FROM users WHERE phone IS NOT NULL`. This can be re-run. It leaves `users.phone` in place.
- **Switch the readers:** change `reminders.py` to read from `contacts`, and add a test that seeds a user with a phone before migrating and checks the reminders output.
- **Verify on a copy:** the `contacts` count should equal the count of non-null `users.phone` (3 here), and I'd read the actual rows.
- **Release B (contract, later):** a separate migration drops `users.phone`, at least a day after the reads have switched. That is the point of no return.
- **Before prod:** take a backup with `cp data/prod.db data/prod.db.pre003` and test restoring it. Both migrations are lossless until B.
- **Watch:** the number of recipients the nightly job returns (should be 3, not 0 or an error), plus the job's error log.

I can write the fixed 003, the `reminders.py` change and the tests now if you want. That would still need your go-ahead before anything runs against prod.