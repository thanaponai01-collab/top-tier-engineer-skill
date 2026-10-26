**The PR was not safe to ship as merged. With the fix below it can ship tonight. The rollback in RELEASE.md was wrong, and I've rewritten it.** I tested everything on copies of `data/app.db` (180 users) against both the code running in production now (`6a913db`) and the PR's code. The live database was not written to.

## What was wrong in `migrations/m0003_plans.py`
1. **It removed the unique constraint on `users.email`.** The table rebuild left out `UNIQUE`, and so did `down()`. Sign-up relies on that constraint to reject a second account for the same email. After the migration, a duplicate sign-up was accepted, and `down` didn't put the constraint back. The tests passed because none of them tried a duplicate email.
2. **Sign-up broke on the old code.** `plan` was `NOT NULL` with no default, so the old code's `INSERT (name, email)` failed. That happens in the gap between `migrate.py up` and the service restarts in `deploy.sh` (the mailer restarts last), and after any code-only revert. The old code also catches every `IntegrityError`, so users would have been told "already has an account" for a new email.

**Fix:** `email TEXT NOT NULL UNIQUE` in both `up` and `down`, and `plan ... DEFAULT 'free'`. I also added `test_duplicate_email`, which fails on Dana's original migration and passes on the fix. All 4 tests pass.

Rehearsal after the fix:
- **Migration:** every row is kept and gets `plan='free'`, and running it twice is harmless.
- **Sign-up checks:** sign-up, duplicate rejection and login work on both the new code and today's code.
- **Undo:** `migrate.py down 2` gives the data back row for row.

## Why the RELEASE.md rollback was wrong
"Revert the merge and run `./deploy.sh`" never touches the schema. The revert removes `m0003` from the tree, so `migrate up` does nothing, and `down 2` can't find anything to undo either (I checked: the database stays at version 3). With the original migration, that left the old code unable to sign anyone up.

With the fix, a code-only revert loses no data and is now the primary rollback. The new RELEASE.md section says:
1. `git revert -m 1 <merge of #57>`, then `./deploy.sh`. The schema stays at version 3.
2. Only if the `plan` column itself has to go: run `python migrate.py down 2` *before* step 1, while `m0003` is still in the tree. Save the list of pro accounts and stop both services first.

**Point of no return:** step 2 run after the first upgrade (from 08:00 tomorrow) deletes the record of who is on pro, and the payments service would keep charging them. A code-only rollback has no point of no return.

## What to watch after deploy
- Sign-up errors, or "already has an account" for new emails.
- `SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1` should return nothing.
- `set_plan` / `plan_of` errors after 08:00.

## Not covered by the rehearsal
The real `deploy.sh` run on the server, live traffic, and the payments service.

I changed `migrations/m0003_plans.py`, `tests/test_accounts.py` and `RELEASE.md`. Nothing is committed, and I deleted the `.release/` working files. Dana should take the migration change into the PR.