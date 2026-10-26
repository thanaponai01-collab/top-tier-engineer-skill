It wasn't safe to ship as written, and the rollback in RELEASE.md was wrong. I've fixed both in the working tree, without committing. The tests pass (6/6). I only opened `data/app.db` read-only and ran every migration on copies of it.

## Problems found

1. **Duplicate accounts.** `m0003_plans` rebuilds the `users` table but the new definition leaves out `UNIQUE` on `email`. After the migration, signing up again with an existing email creates a second account. I reproduced this on a copy of the live DB. `signup()` relies on that constraint to reject duplicates. The PR also deleted `test_one_account_per_email`, the test that would have caught this.

2. **Signups fail during the deploy.** The new `plan` column is `NOT NULL` with no default. `deploy.sh` runs the migration and then restarts the services one at a time, so for a while the old web and mailer processes run against the new schema. Every insert they make without a plan fails with `NOT NULL constraint failed: users.plan`.

3. **The rollback breaks signups and doesn't undo the schema.** "Revert the merge and run `./deploy.sh`" has two problems:
   - `deploy.sh` only runs `migrate.py up`, so the schema change is never reversed.
   - The revert deletes `m0003_plans.py`, which holds the `down()` code, so the migration can't be undone afterwards either.
   
   I simulated this: the old code then failed on every signup with the `NOT NULL` error above. Dana's `down()` also left out `UNIQUE` on email.

## What I changed

- **`migrations/m0003_plans.py`**: put `UNIQUE` back on `email` in both `up` and `down`, and gave `plan` a `DEFAULT 'free'`. With the default, code written before this PR keeps working against the new schema during the deploy and in an emergency.
- **`tests/test_accounts.py`**: restored the duplicate-email test and added two more: one that rolls back to version 2 and checks the old-style signup and uniqueness, and one that checks old code works after the migration. All three fail against Dana's original migration and pass now.
- **`RELEASE.md`**: rewrote the rollback steps in the right order:
  1. Back up the DB.
  2. After 08:00, export the users who have upgraded, because `down` deletes `plan`.
  3. Run `python migrate.py down 2` while the PR's code is still checked out.
  4. Revert the merge and run `deploy.sh`.

I also ran `up` and `down 2` on a copy of the live DB: all 180 users were kept and the schema came back identical to what it is now.

**Before 08:00 tomorrow:** rolling back loses nothing. After that it deletes the record of who pays for `pro`, while the payments service has already charged them. That's why step 2 exports those users first and tells billing.