**Call: ship tonight, as an expand-only release.** Biggest risk was the old invoice worker, which keeps
running on the new schema for up to 40 minutes after the migration; this change leaves its `total`
column in place so it keeps working. No step loses data.

What changed: migration `m0003_total_cents` adds `orders.total_cents` and backfills it with
`ROUND(total * 100)` (a plain cast truncates 126 of the 320 live orders, e.g. 4.35 -> 434). The web
code writes both columns and reads cents; the worker sums cents.

Rehearsed on a copy of `data/shop.db` (the live file was never opened for writing):
- `migrate.py up`: every order's cents equal its rounded dollars, the 19 drafts stay empty.
- Old worker on the migrated copy gives the same invoices as before; old web code can still take an order.
- `migrate.py down 2` after up: schema and every amount back as they were.

Way back: DEPLOY.md's rollback (check out the previous tag, run deploy.sh) only runs `migrate.py up`, so
it would leave `total_cents` in place. That is harmless here because the old code ignores the column,
but the real rollback is: check out the previous tag, `python migrate.py down 2`, restart both
services. I ran that down on the copy; it restores everything.

Watch: refund amounts and the 23:00 invoice run's per-customer totals against last night's.
