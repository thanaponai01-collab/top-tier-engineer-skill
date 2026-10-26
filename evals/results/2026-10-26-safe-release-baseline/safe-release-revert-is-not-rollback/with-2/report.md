**My call: ship tonight only with my fixes. Dana's PR as written would have broken sign-ups, and the rollback in RELEASE.md didn't work.** No rollback step loses data as long as everyone is on `free`. The point of no return is the first `pro` upgrade, at 08:00 tomorrow: after that, removing the `plan` column would lose who has paid. The fixed `down` now refuses in that case instead of dropping it.

### What was wrong (each one reproduced on a copy of `data/app.db`)
| # | Problem | What happened |
|---|---|---|
| 1 | The migration rebuilt `users` without `UNIQUE` on `email` | The same email signed up twice and was accepted. `signup` counts on that constraint to reject duplicates. Tests were green because none of them checked for duplicates. |
| 2 | The documented rollback (revert, then `./deploy.sh`) left the new schema in place | `deploy.sh` only runs `migrate up`, so the database stays at version 3. The old code inserts no `plan`, so **every sign-up failed**, wrongly reported as "already has an account". |
| 3 | `down` dropped `plan` without any check | Run after upgrades start, it would silently forget who is on `pro`. |
| 4 | The table rebuild wasn't atomic | Python's sqlite3 commits `CREATE TABLE` before the copy runs, so a crash mid-migration could leave a half-finished table. |

### What I changed (uncommitted)
- **`migrations/m0003_plans.py`**: replaced the rebuild with a single `ALTER TABLE users ADD COLUMN plan TEXT NOT NULL DEFAULT 'free' CHECK (...)`. RELEASE.md said SQLite can't do this, but it can when the column has a default. The UNIQUE index stays and the change is one atomic statement. `down` drops the column, but refuses while any account is on a paid plan.
- **`tests/test_accounts.py`**: added `test_duplicate_email_rejected`. It fails on Dana's migration and passes on the fix.
- **`RELEASE.md`**: corrected the migration description, added a backup step, and rewrote the rollback.

### Rollback, in one sentence
Revert the merge and run `./deploy.sh`. The old code works fine with the new column still there, at any time, with nothing lost.

**I ran this on a copy of the live database.** The old code (6a913db) signed up and logged in normally on the migrated schema. If the column itself has to go, run `python migrate.py down 2` *before* reverting. On a copy, that gave back exactly the live table definition with all rows kept, and it refused once one user was on `pro`.

### Checks on the copy
- **Tests:** 4 of 4 pass.
- **Migration:** 180 rows before and after, all `free`, 180 distinct emails, index still there; I spot-checked three records.
- **Duplicates:** a duplicate sign-up is rejected again.
- **Live database:** `data/app.db` is byte-identical to before, still at version 2 with 180 users. All testing used copies in `../work/`.

### Still for you to decide before tonight
- **No staged rollout.** This goes to every user at once. The 08:00 pricing-page switch is the only gate on upgrades, so keeping that switch off is your fallback if something looks wrong.
- **No monitoring in the repo.** Three signals worth watching:
  - sign-up errors (`signup` raising ValueError or IntegrityError);
  - the number of users on each plan (`SELECT plan, COUNT(*) FROM users GROUP BY plan`);
  - `set_plan` failures after 08:00.

  If sign-ups fail after the deploy, use the code-only rollback above.
- **Charges happen outside this repo.** `set_plan` writes only to the database, while the payments service charges the card. Nothing here keeps the two in sync or refunds anyone on rollback. I haven't checked this.
- **I didn't deploy or touch the live database**; tonight's deploy is still yours to run.