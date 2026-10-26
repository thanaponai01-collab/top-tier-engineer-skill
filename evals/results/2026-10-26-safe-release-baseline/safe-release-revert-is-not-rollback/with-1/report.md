**Verdict: ship it with my fixes in. Without them, hold.** Both of the PR's problems were in the migration. With the fixes, the code rollback loses no data. Running `migrate.py down` stops being lossless once someone upgrades to `pro` at 08:00 tomorrow, because it would erase who has paid.

## What was wrong

1. **Duplicate sign-ups were accepted.** `m0003_plans` rebuilds the `users` table and left `UNIQUE` off `email`. `users.signup` relies on that constraint to reject a duplicate, so it stopped doing so. On a copy of `data/app.db`, signing up `<email>` again went through.
2. **The rollback in RELEASE.md broke all new sign-ups.** "Revert the merge and run `./deploy.sh`" leaves migration 3 applied, because `deploy.sh` only runs `migrate up`. `plan` was `NOT NULL` with no default, and the old code inserts users without a plan. I ran it: every new sign-up on the old code failed, with the misleading message "<email> already has an account." The same failure would also hit tonight's deploy in the gap between `migrate up` and the web restart.
3. **`down` was lossy and unguarded.** It drops `plan` with no warning. Its rebuilt table also lacked `UNIQUE`.

## What I changed (not committed)

- **`migrations/m0003_plans.py`:**
  - The rebuilt table keeps `email UNIQUE`.
  - `plan` now defaults to `'free'`.
  - The rebuild and the version bump now happen in one transaction, so a crash can't leave the database half-migrated.
  - `down` refuses to run while any account is `pro`.
- **`tests/test_accounts.py`:** three new tests: a duplicate email is refused, an insert without a plan still works, and `down` won't erase paid plans. All three fail on Dana's version of the migration. With the fix, all 6 tests pass.
- **`RELEASE.md`:** rewrote the rollback section and added a backup step and the queries to watch.

## How I checked it

All of this ran on a copy of the database. `data/app.db` is still at schema version 2 and was not touched.

| Step | Forward | Backward | Loses data? |
|---|---|---|---|
| Migrate to version 3 | Rebuilds `users` with a `plan` column | Revert the code only and leave the schema | No |
| First upgrade to `pro` (08:00) | `plan = 'pro'` | Same code-only revert | **`down 2` would**, so it now refuses |

- **Forward:** 180 rows before and after, every existing column identical, all accounts `free`, and SQLite's integrity check passes.
- **Rollback:** I set one account to `pro`, then ran the previous release's code against the migrated copy. Sign-up, login and duplicate rejection all worked, and the `pro` account kept its plan. Re-deploying afterwards found the plans intact.

**Rollback in one sentence:** revert the merge, push, and run `./deploy.sh`, leaving migration 3 in place. I ran this on the copy, not in production.

## Before or during tonight

- **Back up first:** `cp data/app.db data/app.db.pre-m0003`, with the services stopped.
- **What to watch** (there's no metrics setup in the repo, so these are manual checks):
  - "already has an account" errors for emails that are actually new;
  - `SELECT plan, COUNT(*) FROM users GROUP BY plan` should show all `free` until 08:00;
  - the duplicate-email query in RELEASE.md should stay empty.
- **Not covered by my review:**
  - `accounts-mailer` isn't in this repo, so I couldn't check whether it reads `users`.
  - Upgrades charge cards through a payment service outside this repo, and that goes live at 08:00. Whether to turn it on is your call or Dana's; the pricing page is the only thing gating who can upgrade.
- I did not deploy.