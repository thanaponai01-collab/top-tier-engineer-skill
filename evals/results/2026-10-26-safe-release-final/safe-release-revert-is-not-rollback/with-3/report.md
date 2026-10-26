**Verdict: it can ship tonight with the fix I made. As Dana merged it, it was not safe, and the rollback in RELEASE.md was wrong.**

I tested the migration and its rollback on copies of `data/app.db`. I ran them with today's production code (`6a913db`, the commit before the merge, since `HEAD` already has the merge) and with the new code. The live database was never written to: it's still at schema version 2 with 180 users.

**What was wrong in `migrations/m0003_plans.py`:**
1. **The migration removed the unique rule on `users.email`.** The rebuilt table left out `UNIQUE`, so after the migration the same email could sign up twice. Running the migration's undo step didn't bring the rule back either. The tests didn't catch it because none of them tries a duplicate sign-up.
2. **Every sign-up from today's code would have failed.** `plan` was `NOT NULL` with no default, and today's `signup` doesn't set a plan. This hits in two cases: between the migration and the service restart, and after any rollback that only reverts the code. Users would also have seen the wrong message: the insert error is reported as "already has an account".

**Fix (only that file changed):** the rebuilt table keeps `UNIQUE` on email, `plan` defaults to `'free'`, the undo step puts `UNIQUE` back, and both steps clear out a half-built table left by an earlier failed run. Re-run on a copy:
- the migration is safe to run twice;
- the new code works on the migrated data, and so does today's code;
- the undo step gives back every row and the original constraints;
- the 3 unit tests pass.

**Rollback (I rewrote it in RELEASE.md):** "revert the merge and run `./deploy.sh`" didn't undo anything in the database, because `deploy.sh` only runs `migrate.py up`. With Dana's migration, that revert would have left sign-ups broken and duplicate emails allowed. The rollback is now:
1. **Code only, no data lost:** `git revert -m 1 <merge commit of #57>`, push, `./deploy.sh`. I tested this: today's code works with the `plan` column left in place.
2. **Only if the schema has to go:** snapshot the database, then `python migrate.py down 2`. **This deletes every account's plan.** Once upgrades go live at 08:00 tomorrow, nothing will record who is on `pro` and was charged. After that time, treat this step as the point of no return. The test reported it lossless only because no account had upgraded yet.

**What to watch after the deploy:**
- sign-up errors, especially "already has an account" for new emails;
- `IntegrityError` on `users` in the web or mailer logs;
- duplicate emails: `SELECT email FROM users GROUP BY email HAVING COUNT(*)>1` should return nothing.

**What I couldn't check:**
- **`accounts-mailer`:** its code isn't in this repo, and it keeps running on the rebuilt table until it restarts after its current batch.
- **The payments service** that upgrades charge through.
- **The real deploy:** live traffic during the table rebuild, which locks the table briefly, and the server's config.

Uncommitted changes: `migrations/m0003_plans.py` and `RELEASE.md`. I deleted the helper's `.release/` working folder.