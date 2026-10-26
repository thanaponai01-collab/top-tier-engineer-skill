Not safe to ship as merged, and the rollback in RELEASE.md was wrong. I've fixed both and left the changes uncommitted.

## Problems in the PR

1. **The migration removed the one-account-per-email rule.** `m0003_plans` rebuilds `users` without `UNIQUE` on `email`. `signup()` only rejects a repeat email when the database refuses the insert, so after deploy the same email could sign up any number of times. The same PR deleted `test_one_account_per_email`, which is why the tests were still green. `down()` had the same gap.

2. **The rollback would have broken sign-ups.** `plan` was `NOT NULL` with no default. After "revert the merge commit and run `./deploy.sh`", the old `signup()` doesn't supply a `plan`, so every new sign-up would fail. Running `deploy.sh` doesn't undo the schema change: it only runs `migrate.py up`, and once the revert removes `m0003_plans.py` there is nothing left to undo it with. The database stays at version 3.

## Changes

- `migrations/m0003_plans.py`: put back `email TEXT NOT NULL UNIQUE` in both `up()` and `down()`, and gave `plan` a default of `'free'`.
- `tests/test_accounts.py`: restored the duplicate-email test.
- `RELEASE.md`: rewrote the rollback section:
  - **Default rollback:** revert only the code and leave the `plan` column in place. The old code works against the new schema and no plans are lost.
  - **Full schema rollback:** `python migrate.py down 2` has to run before the revert. It deletes everyone's plan, including who has paid for `pro` after tomorrow's 08:00 launch, so export the paying accounts first.
  - **Before deploying:** back up `data/app.db`.
  - **Re-landing:** keep the migration name `m0003_plans`, because the database will already say version 3 and would skip a different migration with that number.

## Checks run

- Tests: 4 pass.
- On a **copy** of the live database (180 users, no duplicate emails): the migration applied cleanly, all 180 users came through as `free`, and the email rule was in place. Running the old code against the migrated copy, sign-up worked and a duplicate email was rejected. `down 2` also worked on the copy.
- I didn't change the live `data/app.db`. It's still at version 2, and my scratch copies are deleted.

**Minor, not fixed:** the migration isn't fully atomic. If it fails partway, a leftover `users_new` table can block a re-run, though the live data stays intact. It's worth knowing about if the deploy errors out.