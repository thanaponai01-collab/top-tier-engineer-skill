# Release 2026-10-26: paid plans (PR #57, Dana)

- Every account gets a plan, `free` until it upgrades; `pro` is $12/month.
- Migration `m0003_plans` adds `users.plan` (table rebuild, since SQLite can't add a CHECK column
  to an existing table).
- `app/billing.py`: `set_plan`, `plan_of`. Upgrades go live on the pricing page at 08:00 tomorrow.
- Tests: green (`python -m unittest discover tests`).

Rollback: revert the merge commit and run `./deploy.sh`.
