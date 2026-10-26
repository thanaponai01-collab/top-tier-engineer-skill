The PR wasn't safe to ship as it was, and the rollback in RELEASE.md was wrong. I've fixed both in the working tree. Nothing is committed, and `data/app.db` hasn't been touched: it's still at schema version 2 with 180 users.

## What was wrong

**1. The migration dropped the unique constraint on email.** `m0003_plans` rebuilds the `users` table, and the new table declares `email TEXT NOT NULL` without `UNIQUE`. `users.signup` relies on that constraint to raise "already has an account". After the deploy, the same email could sign up any number of times, with nothing reported. `down()` had the same omission. The tests stayed green because none of them tried a duplicate.

**2. The rollback in RELEASE.md would have broken sign-ups.** "Revert the merge commit and run `./deploy.sh`" only rolls back the code. `deploy.sh` only runs `migrate.py up`, so the schema stays at version 3. The new `plan` column was `NOT NULL` with no default, so the old sign-up code (which doesn't fill in `plan`) would fail on every insert. Undoing the migration doesn't help either: the revert deletes `m0003_plans.py`, so `down` can't run after it. And once upgrades go live at 08:00, `down` would drop the only record of who is paying for `pro`.

## What I changed

- **`migrations/m0003_plans.py`:** `email` is `UNIQUE` again in both `up` and `down`. `plan` now has `DEFAULT 'free'`, so the pre-PR code keeps working against the new schema. That makes a code-only rollback safe.
- **`tests/test_accounts.py`:** three new tests:
  - a duplicate email (differing only in case and spaces) is rejected
  - the old insert, which doesn't fill in `plan`, works after the migration and gets `free`
  - `down` keeps email unique
- **`RELEASE.md`:**
  - back up the database before deploying
  - the rollback is code-only and that's intended: leave the schema at version 3
  - don't run `migrate.py down 2` once upgrades are live
  - if the column really has to go, export the paying users first and run `down` before reverting

## Checks

- **Tests:** all 6 pass.
- **Copy of the live database:** I ran `up` then `down 2` on a copy. `up` kept all 180 users with 180 distinct emails, all set to `free`, with `UNIQUE` in place. `down` brought it back to the original table shape with all 180 rows.

## Not fixed, but worth knowing

- Billing happens in a separate payments service, and upgrades go live on a different schedule (08:00) from this deploy. So a "pro" row in this database and an actual charge can get out of sync. That can't be checked from this repo.
- The migration isn't fully atomic: the `CREATE TABLE users_new` step runs outside the transaction. If `up` crashes partway, a leftover `users_new` table will make it fail on the retry. It's easy to clean up by hand, and with the backup step it's low risk.

These fixes are only in Dana's migration and tests, so they need to land in the branch before tonight's deploy. I left that to you since you said not to commit.