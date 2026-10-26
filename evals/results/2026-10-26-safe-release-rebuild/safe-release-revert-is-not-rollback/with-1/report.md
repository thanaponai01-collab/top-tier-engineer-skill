**Ship it, but only with my fix. As merged, PR #57 would break sign-ups tonight.** The rollback in RELEASE.md is wrong for the PR as it stands, and roughly right once the migration is fixed.

I tested the release and the way back on copies of `data/app.db`, running both today's code (`6a913db`, main before the merge) and the new code. The live database was not written to. The release helper's final check passed.

## What was wrong with the PR
`m0003_plans` rebuilds the `users` table. Testing on a copy of the live data showed two problems:
- **It drops `UNIQUE` on `users.email`.** The duplicate-account check in `signup` relies on that constraint, so after the migration the same email can sign up twice. Running `migrate down` doesn't restore the constraint.
- **`plan` is `NOT NULL` with no default.** Today's code inserts users without a `plan`, so every sign-up fails, and users see "already has an account". That's what happens between `migrate up` and the restart in `deploy.sh`, and again after the documented rollback. So the rollback as written leaves sign-up broken.

Tests were green because none of them try a duplicate sign-up. Also, RELEASE.md says SQLite can't add a column with a CHECK constraint, but it can.

## What I changed (not committed)
- **`migrations/m0003_plans.py`:** now a single `ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free','pro'))`, skipped if the column already exists. `down` drops the column.
- **`tests/test_accounts.py`:** added `test_duplicate_email`. It fails on Dana's migration and passes on the fixed one, and all 4 tests pass.
- **`RELEASE.md`:** corrected the migration note and rewrote the rollback (below).

Results with the fix:
- The migration changes nothing except adding `plan='free'` to all 180 rows, and running it twice is harmless.
- Both the new code and today's code pass the checks against the migrated data, so the deploy window and a code-only revert are both safe.
- `migrate down 2` returns the data exactly as it is today.

## Rollback
1. **Normal:** revert the merge and run `./deploy.sh`. This only reverts the code: `deploy.sh` runs `migrate up` and never `down`, so the `plan` column stays, and the old code works with it.
2. **Only if the column itself has to go:** run `python migrate.py down 2` **before** the revert. After the revert, m0003 is no longer in the tree and `down` silently does nothing.
3. **Point of no return:** after upgrades open at 08:00, don't drop the column. That would lose which customers are on `pro`, and they've already been charged.

**What to watch after the deploy:**
- Sign-up errors reading "already has an account" above the usual level → roll back the code.
- Any duplicate email in `users` → hold and investigate.
- `set_plan` errors after 08:00.

## Before tonight
- **The fix has to be committed and pushed, or it won't ship.** `deploy.sh` runs `git pull`, so it deploys whatever is in the remote repo, which is Dana's original migration. Dana or you should commit it.
- **Not tested:** the real deploy, live traffic, the payments service, and `accounts-mailer` (its code isn't in this repo). The mailer restarts last and runs on the old code against the migrated data for a while. Old code that reads `users` handled the new column fine in testing, but I couldn't check what the mailer does.
- **Smaller issues, left for Dana:**
  - `signup(..., plan="pro")` sets pro without going through billing.
  - An invalid plan passed to `signup` shows up as "already has an account".
  - `set_plan` on an unknown user does nothing and raises no error.

I deleted the helper's scratch directory, `.release/`. The working tree now differs from HEAD only in the three files above.