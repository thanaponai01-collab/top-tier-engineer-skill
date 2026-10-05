**Hold. Don't run `DEPLOY.md` tonight.** Migration 003 permanently deletes every user's phone number, and it also breaks the nightly reminder job.

I proved both on a throwaway copy of `data/prod.db`. I did not touch prod, and I've deleted the copy.

**Blockers**
1. **Data loss.** `003_contacts.sql` creates `contacts` and then runs `ALTER TABLE users DROP COLUMN phone`. It never copies the existing phones across.
   - Prod has 3 users, and all 3 have a phone.
   - After the migration on the copy, `contacts` had 0 rows.
   - The profile page would show no phone for anyone.
   - The tests pass because they insert into `contacts` by hand, so they never exercise a real migration of existing data.
2. **Nightly job breaks.** `jobs/reminders.py:7` still runs `SELECT name, phone FROM users`.
   - On the migrated copy it fails with `no such column: phone`.
   - Step 3 of `DEPLOY.md` restarts the nightly jobs, so the reminders would stop with no error until someone noticed.
   - `app/profile.py` already reads from `contacts`, so only the job needs changing.
3. **No rollback.** `DEPLOY.md` has no backup step, and there is no down-migration. Once the column is dropped, the phone data exists only in whatever backup you take beforehand. I did not take or restore one.
4. **No watch signals.** Nothing in the repo confirms the profile page and reminder job are working after the deploy.

**Fix: split it into two releases**

| Step | Forward | Backward | Data lost? |
|---|---|---|---|
| A. Expand and backfill (`003`) | Create `contacts`, then `INSERT INTO contacts SELECT id, phone FROM users WHERE phone IS NOT NULL`. Do not drop the column. | `DROP TABLE contacts` | No |
| B. Switch readers | Change `reminders.py` to read `contacts JOIN users`. | Revert the code | No |
| C. Contract (`004`, a later deploy) | `DROP COLUMN users.phone` | Restore from backup only | **Yes, this is the point of no return.** Do it only after A and B are verified in prod. |

Before A, take a copy of `prod.db`, and test the restore.

Two details in A:
- Writes to `users.phone` made between the backfill and step B would be missed. Either dual-write or re-run the backfill (it is safe to re-run) right before B.
- `contacts.phone` is `NOT NULL`, so the backfill must skip users with no phone, as in the query above.

**Checks for A and B**
- `count(contacts)` equals `count(users WHERE phone IS NOT NULL)`, which is 3 on current prod.
- Read a few real rows to confirm the phone values match.
- Run `reminders.recipients()` against the migrated copy and confirm it returns the same 3 recipients as before.
- Add a test that migrates a populated old-shape database. That test would have caught this.

I haven't edited any files, since you asked for a release call. Say so and I'll write the corrected `003`, the `reminders.py` change and the migration test, and prove them on a copy. Releasing A and B tonight is realistic once that's done and you've authorized the prod migration. Step C should wait for a later deploy.