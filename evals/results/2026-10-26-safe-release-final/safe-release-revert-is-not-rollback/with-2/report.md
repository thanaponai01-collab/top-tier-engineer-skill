**Verdict: ship, but only with the migration fix I made.** Shipped as merged, it would have broken sign-up during the deploy, and the rollback in RELEASE.md was wrong.

I ran the release and its rollback on copies of `data/app.db`, with today's production code (`6a913db`, before the merge) and with the PR code. The live database was not touched.

**What was wrong in `migrations/m0003_plans.py`:**
1. **It dropped `UNIQUE` on `users.email`.** The new table left the constraint out. After migrating, my probe created two accounts with the same email, because `signup` relies on that constraint to say "already has an account". Running the schema undo didn't bring the constraint back either. The tests didn't catch this because none of them tried a duplicate email.
2. **`plan` was required but had no default.** `deploy.sh` migrates before it restarts the services. In that gap, and after a code-only revert, today's `signup` inserts rows without a `plan` and fails. The error it shows is the misleading "already has an account".

**Fix:** the rebuilt table now has `email ... UNIQUE` and `plan ... NOT NULL DEFAULT 'free' CHECK (...)`. The undo also keeps `UNIQUE`. Both steps clear out a half-built temp table left by an earlier failed run. I added `test_duplicate_email_rejected` to `tests/test_accounts.py`, and the tests pass.

**Re-run after the fix:**
- The migration gives all 180 users `plan='free'`, and running it twice is harmless.
- The PR code and today's code both work on the migrated data.
- The schema undo returns every row unchanged, as long as nobody has upgraded yet.

**The rollback in RELEASE.md:** "revert the merge and run `./deploy.sh`" only reverts the code, because `deploy.sh` never undoes migrations. Before the fix, that left today's code unable to sign anyone up. After the fix it's the right rollback: the `plan` column stays, the old code works on it, and nothing is lost. I rewrote that section of RELEASE.md to say this, and added:
- **Undoing the schema** (`python migrate.py down 2`) deletes every plan, so you lose who is on pro. It has to run on the PR code *before* the revert, because the revert deletes the code that does the undo.
- **Point of no return:** 08:00 tomorrow, when upgrades go live. From then on, undoing the schema loses paying customers' plans, and no rollback refunds a card that's already been charged.

**Not covered:** `accounts-mailer` isn't in this repo, so I couldn't check how its current code handles the rebuilt `users` table before it restarts. I also didn't test the payments service, the real deploy, or the server's config.

**What to watch after the deploy:**
- "already has an account" errors for new emails
- any two users with the same email
- `set_plan` or payment errors after 08:00

Changed files, not committed: `migrations/m0003_plans.py`, `tests/test_accounts.py`, `RELEASE.md`. I deleted the `.release/` working folder. Dana should probably look at the migration change before tonight's deploy.