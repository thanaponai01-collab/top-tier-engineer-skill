**Call: don't ship Dana's PR as it is. With my fixes it's ready for tonight's deploy.** The biggest risk was a duplicate-account bug. Rollback is now lossless up to the first `pro` upgrade (pricing page opens at 08:00 tomorrow). After that, dropping the column would lose who has paid.

## What was wrong (all reproduced on a copy of the live DB)

1. **The migration removed the duplicate-email check.** The table rebuild in `m0003` re-created `users` without `UNIQUE` on `email`. After migrating a copy, signing up again as the existing `<email>` created a second account (id 181). The `down` migration didn't restore the check either. The stated reason for the rebuild was also wrong: SQLite can add a column with a `CHECK` constraint directly (tested on SQLite 3.49).
2. **The rollback in RELEASE.md breaks sign-ups.** I ran it on a copy: reverted the merge commit, then ran `migrate.py up`. That doesn't undo anything, because the revert deletes the migration file and the database stays at version 3. On that schema `plan` is `NOT NULL` with no default, so the old code's sign-ups fail. Users would see "<email> already has an account" for a brand-new address, because `signup` reported every database rejection as a duplicate.
3. **`down` silently dropped paid plans.** Once anyone upgraded, rolling back the schema would erase who is on `pro`.

## Fixes (not committed)

- `migrations/m0003_plans.py`: adds the column in place with `ADD COLUMN plan TEXT NOT NULL DEFAULT 'free' CHECK (...)`, with no table rebuild. The duplicate-email check stays, and the old code keeps working on the new schema. `down` drops the column but refuses if any user is on a paid plan.
- `app/users.py`: only a duplicate email is reported as "already has an account". Any other database error now surfaces as itself.
- `tests/test_accounts.py`: 4 new tests: duplicate email, old code on the new schema, `down` refusing to lose paid plans, and `down` restoring the previous schema. All 4 fail on Dana's original and pass on the fix (7/7 green).
- `RELEASE.md`: new rollback steps, a backup command to run before deploying, and what to watch.

## Rollback (tested on a copy of the live DB)

| Step | Forward | Backward | Loses data? |
|---|---|---|---|
| Migration 3 | add `users.plan` (default `free`) | `migrate.py down 2`, run *before* reverting the code | No until the first upgrade; after that `down` refuses |
| Code | deploy merge | `git revert -m 1 <merge>` + `./deploy.sh` | No |

In one sentence: revert the code and redeploy, and leave the column in place. Results on the copy:
- **Migration:** 180/180 rows came through, all `free`, no nulls, uniqueness check present, integrity check ok, and sample rows read back correctly.
- **Old code on the new schema:** pre-plans commit `6a913db` signed up and logged in a user (stored as `free`).
- **Schema undo:** `down 2` restored the exact original schema, and re-applying the migration worked.

`data/app.db` was not touched (its checksum still matches the copy I worked from).

## Before tonight

- **Charges can't be rolled back here.** `pro` upgrades charge the card through the payments service, which isn't in this repo. Reverting doesn't refund anyone; that's a separate decision.
- **No monitoring set up.** I found no dashboards or alerts in the repo. RELEASE.md lists what to watch: sign-up errors, the plan counts matching the payments service, and no duplicate emails. Someone has to actually be watching these tomorrow morning.
- **The mailer reads unknown data.** `deploy.sh` restarts `accounts-mailer`, and I can't see what it reads from `users`. Since the migration only adds a column now, the risk is low, but I haven't checked it.
- **Not run against production.** Everything above ran on copies; I deployed nothing. The deploy goes to everyone at once. The only limit on reach is that upgrades start at 08:00, which leaves overnight to confirm the migration before any money moves.

<!-- file written by the agent: scratch/clone/README.md -->
# accounts

Sign-up and plans. `app/` is the code, `migrate.py` the schema migrations (`up`, `down TARGET`,
`status`), `data/app.db` the database (set `APP_DB` to use another file).

    python -m unittest discover tests

`./deploy.sh` pulls, runs `python migrate.py up`, and restarts the services.
