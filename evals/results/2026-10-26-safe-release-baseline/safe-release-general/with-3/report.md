# PAY-31: ready to ship at 21:00 once the code is in git; rollback tested and loses no data

**Call: ship once these changes are in the branch `deploy.sh` pulls.** I haven't committed anything, and `deploy.sh` starts with `git pull`. It deploys what's in the repo, not this working tree. Also, `fixture/` isn't a git repo, so run here, `deploy.sh` stops at `git pull` before migrating anything. The documented rollback (`git checkout <previous tag>`) doesn't work here either.

- **Biggest risk:** the overlap window. Old web code runs for a few seconds after the migration, and the old worker for up to 40 minutes. I tested that both still behave correctly (details below).
- **Data loss on rollback:** none at any step of this release. The step that would lose data is a later, separate release that drops the old dollar column (`total`). All it would lose is the dollar copy. No existing order has a fraction of a cent (0 rows), so cents keep every value.
- **Who's affected:** every order goes to 100% at once. There's no canary or feature flag. That's acceptable only because the rollback is tested and loses nothing, but it's your call.

## What changed
- `migrations/m0003_total_cents.py` (new): adds `total_cents INTEGER` alongside `total`. It fills it in batches of 500 and is safe to re-run. It also adds two triggers that copy anything old code writes to `total` into `total_cents`. `down()` removes the triggers and the column.
- `app/orders.py`: the bug fix. Amounts are converted once to cents, and refunds subtract whole cents. It still writes `total` (as cents ÷ 100) for old code. Callers still pass and get back dollars, so the function signatures don't change.
- `worker/invoices.py`: adds up cents instead of floats.
- `check_cents.py` (new): read-only check that the two columns agree; this is the signal to watch.
- `tests/test_orders.py`: 4 new tests, covering the cent-off refund, old-code writes, the dollar column still being correct, and rollback.

What this release carries: one migration (schema 2 → 3) and two triggers. No config changes, secrets, dependencies or flags.

## Evidence
- **Tests:** all 8 pass. The new refund test fails on the original code (`0.19999999999999998 != 0.2`), so it really catches the bug.
- **Rehearsal on a copy of `shop.db`:**
  - **Forward:** all 301 non-NULL totals were filled. The cents add up to 663,726, the same as the float sum × 100. Drift and missing cents are both 0. The 19 NULL totals are drafts and stay NULL. Example: order 2's `34.089999999999996` became `3409`.
  - **Old worker on the new schema:** its invoices for every day match the new worker's exactly.
  - **Rollback (`down 2`):** the orders table is byte-for-byte identical to before (same checksum). Re-applying `up` gives clean results again.
- **Live DB:** I only opened it read-only. It's still at schema 2.

## Migration steps
| Step | Forward | Backward | Data lost from here? |
|---|---|---|---|
| Expand + fill (this release) | `migrate.py up` → schema 3 | `migrate.py down 2` | No |
| Read from cents (this release) | new code | redeploy previous code | No: `total` is still written |
| Contract (later, separate release) | drop `total` and the triggers | none | **Yes**: the dollar column is gone |

## How to back out
In one sentence: roll the code back to the previous tag, and optionally drop the new column. I ran the column-drop step on a copy, not the code rollback, because there's no git or systemd here.

1. *(Before 21:00, recommended — I didn't run it because it writes to the live box)* `sqlite3 data/shop.db ".backup data/shop.pre-pay31.db"`
2. Code only: `git checkout <previous tag> && ./deploy.sh`. The old code runs fine on schema 3, and the triggers keep cents in sync.
3. To also remove the column: run `python migrate.py down 2` **before** step 2, while the new code is still checked out. The old checkout doesn't have the m0003 file, so `down` can't undo it from there.

## What to watch (21:00 → after the 23:00 invoice run)
1. `python check_cents.py`: run it after the migration and again around 21:45, once the worker has restarted. Roll back if `drift` or `missing_cents` is above 0 (it exits with 1).
2. `paid_with_float_dust` in the same output: it's 0 now and must stay 0. This is the ticket's symptom: orders stuck as "paid" with a tiny leftover amount.
3. Errors from `shop-web` and `shop-worker` (journal or `systemctl status`), and whether the 23:00 run produces invoices. There's no error-rate monitoring in the repo, so I can't confirm that signal exists. That one is on you to check.