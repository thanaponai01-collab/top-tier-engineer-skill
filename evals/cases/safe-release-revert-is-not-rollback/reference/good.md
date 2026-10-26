**Hold as written; ship after the three fixes below (made).** Biggest risk: the documented rollback
breaks every sign-up.

1. Rollback "revert and redeploy" is not a way back. deploy.sh only runs `migrate.py up`, so the
   rebuilt table stays, and the old `signup` inserts no plan into `plan TEXT NOT NULL` with no
   default: every sign-up fails after the rollback. Fixed: `plan` now has `DEFAULT 'free'`; tried the
   old code on a migrated copy, it signs up fine.
2. The rebuild dropped `UNIQUE` on `users.email`, so one email could hold several accounts. Restored
   in both up and down; a duplicate sign-up is refused again on the copy.
3. `down` drops the plan column: after the first upgrade at 08:00 tomorrow, rolling back loses who
   is on pro. That is the point of no return; back up `users(id, plan)` before running down.

Rehearsed on a copy of `data/app.db` (live file untouched): up, old and new sign-up, `migrate.py down 2`,
all 180 accounts identical. Rollback: `python migrate.py down 2` then deploy the previous tag.
