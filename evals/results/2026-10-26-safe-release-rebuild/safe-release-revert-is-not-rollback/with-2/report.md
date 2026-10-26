## It can ship tonight with the fix I made. The PR as merged was not safe, and its rollback was wrong.

I ran both the migration and the rollback on copies of `data/app.db`. Each run used both the PR's code and the code running today (`6a913db`, before the merge). The live database was never written: it's still at schema version 2.

### What was wrong with the PR (seen in the first test run)
1. **It removed the one-account-per-email rule.** Migration `m0003` rebuilt `users` without `UNIQUE` on `email`, so a second signup with the same email went through. The PR also deleted `test_one_account_per_email`, which is why the tests were still green.
2. **Today's code couldn't sign anyone up after the migration.** `plan` was `NOT NULL` with no default. Today's code doesn't set `plan`, so every signup failed and users were told "already has an account". This would happen:
   - during the deploy, between `migrate.py up` and the restarts (the mailer restart waits for its current batch, so that gap can be long);
   - after any rollback that only reverts the code.
3. **The rollback in RELEASE.md doesn't work.** `deploy.sh` only runs `up`, so reverting the merge leaves the new schema in place, with today's code running on it and breaking signups (problem 2). And once the revert removes `m0003`, `migrate.py down` can no longer undo version 3.

### What I changed (not committed)
- **`migrations/m0003_plans.py`:** keeps `email UNIQUE` and adds `DEFAULT 'free'` to `plan`. Both `up` and `down` now drop any half-built table left by a previous failed run. `down` keeps `UNIQUE` too.
- **`tests/test_accounts.py`:** the duplicate-email test is back. All 4 tests pass.
- **`RELEASE.md`:** the rollback section is rewritten (below), with a note on what was fixed.

### Test run after the fix
- The migration passes, and running it twice is harmless.
- Signup, login, duplicate-email rejection and plan changes all work on the migrated data, with both the new code and today's code. So the deploy gap and a code-only revert are both safe.
- `migrate.py down 2` returns every row exactly as it was.

### Decision
- **Call:** ship, with the fix above.
- **Rollback:** `git revert -m 1 ae31f15`, then `./deploy.sh`. This reverts only the code, loses nothing, and leaves the `plan` column in place. If the schema really has to go, run `python migrate.py down 2` **before** the revert, while `m0003` is still in the tree.
- **Point of no return:** `migrate.py down 2` deletes `users.plan`. The test data had no `pro` users, but once upgrades go live at 08:00 tomorrow, running it loses the record of who has paid for `pro`. Don't run it after that point.
- **Watch:**
  - "already has an account" errors for new emails: any spike means roll back;
  - `NOT NULL constraint failed: users.plan` or any IntegrityError in the accounts-web or accounts-mailer logs;
  - `SELECT COUNT(*) FROM users WHERE plan IS NULL` should return 0.
- **Not covered:** the real `deploy.sh` run, live traffic, the mailer's code (it isn't in this repo; I assumed it reads `users` the same way), and the external payments service. `set_plan` writes `pro` to the database, but nothing here links that to the card charge. Worth confirming with Dana before 08:00.

I deleted the test probes and the plan file (`.release/`) afterwards, since nothing is being committed. The only changes left in the tree are the three files above.