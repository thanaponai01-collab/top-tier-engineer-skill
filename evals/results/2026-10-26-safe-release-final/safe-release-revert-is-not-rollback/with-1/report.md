**Verdict: it's safe to ship with the fixes I've made. As merged it was not, and the rollback in RELEASE.md was wrong.**

## What was broken (all reproduced on copies of `data/app.db`)

I tested against the code that's live now (`6a913db`, before the merge), not just the PR.

1. **The migration removed "one account per email."** `m0003_plans` rebuilt `users` without `UNIQUE` on `email`. `users.signup` relies on that rule to reject a duplicate address, so duplicate sign-ups went through. The PR also deleted `test_one_account_per_email`, which is why the tests were still green.
2. **`plan` was `NOT NULL` with no default.** Between `migrate.py up` and the restarts, the old web and mailer processes keep running, and their sign-ups don't supply a plan. Every one of those sign-ups failed. The same would happen after the RELEASE.md rollback (revert plus `deploy.sh`), because `deploy.sh` only migrates *up*. The column stays and the reverted code can't insert into it.
3. **`down` didn't put the email rule back either.** So even a full schema rollback left duplicates allowed.

## What I changed (not committed)

- **`migrations/m0003_plans.py`:** keeps `UNIQUE` on email, adds `DEFAULT 'free'` to `plan`, and `down` now restores `UNIQUE` too. Both steps first clear any half-built table left by a run that died midway.
- **`tests/test_accounts.py`:** I put back `test_one_account_per_email`. All 4 tests pass.
- **`RELEASE.md`:** the rollback is corrected (see below), and there's a note to back up `data/app.db` before deploying.

## Re-test after the fixes

- The migration runs cleanly, and running it twice is harmless. All 180 users get `free`.
- Both the new code and the live code work on the migrated data: sign-up, rejecting a duplicate email, login, and upgrading a plan.
- `migrate.py down 2` gives the data back row for row.
- The live `data/app.db` was never written; it's still at version 2 with 180 users.

## Corrected rollback

- **Default, loses nothing:** `git revert -m 1 <merge>`, then `./deploy.sh`. The `plan` column stays, and the live code works fine with it.
- **Only if the column itself must go:** run `python migrate.py down 2` **before** the revert. The revert deletes the m0003 file, so `down` can't undo it afterwards. This deletes every account's plan. After 08:00 tomorrow that includes the record of who paid for `pro`, so **this is the point of no return.**

**What to watch after the deploy:** sign-up errors in the web or mailer logs, any two users with the same email, and `plan_of` returning nothing for an existing user. Any of these means use the default rollback.

**Not covered:** `accounts-mailer` and the payments service aren't in this repo, so I couldn't test them, and nothing here exercises the real deploy or the server's config. Note that `set_plan` changes the plan without charging anyone; I'm assuming the payments service does the charging.