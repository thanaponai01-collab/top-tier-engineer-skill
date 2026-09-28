# Safe Release — fixture/

**No-go.** Biggest risk: migration `002_migrate_total_to_cents.sql` drops the `total` column in the
same script that adds and backfills `total_cents`, and `app.py` switches to reading `total_cents` in
that same deploy. Any rollback loses data, at that step, and it's untested.

## Migrations in this release

| step | forward | backward | lossy from here? |
|---|---|---|---|
| 001 add notes column | `ALTER TABLE orders ADD COLUMN notes TEXT` | drop the column | no — purely additive, nullable, nothing reads it yet. 001 is safe on its own. |
| 002 add total_cents | `ALTER TABLE orders ADD COLUMN total_cents INTEGER` | drop total_cents | no, if this were its own deploy |
| 002 backfill | `UPDATE ... SET total_cents = ROUND(total*100)` | re-derive from total | no, if total still existed |
| 002 drop total | `ALTER TABLE orders DROP COLUMN total` | **none** | **yes — this is the point of no return** |

`002_migrate_total_to_cents.sql` runs all three of those in one script, and the same release
switches `app.py` to read `total_cents`. That's expand, backfill and contract all in one migration
and one deploy — never separate deploys, so there is no gap to verify the backfilled data or watch
before the old column disappears. Proven with `test_migration.py`: after running both migrations,
`PRAGMA table_info(orders)` no longer lists `total` — the dollar-denominated data is gone, and the
only surviving record is whatever got written into `total_cents`.

`MIGRATION.md` says "revert the commit" is the rollback and calls it "safe and reversible like any
other code change." That's false and untested: reverting `app.py` and the migration file does not
put the dropped `total` column's data back. Once `002` has run, there is no way back for that data.

## Fix

Split `002` into its own three deploys: (1) add `total_cents` alongside `total`, ship, verify a
sample of backfilled rows against `total`; (2) switch reads to `total_cents`, watch; (3) drop `total`
in a later, separate deploy, only once (1) and (2) have been running cleanly. Only step (3) is the
point of no return, and only step (3) needs sign-off with that framing.

## 001, for contrast

`001_add_notes_column.sql` is fine as-is: purely additive, nullable, no backfill, nothing depends on
it yet. It is reversible on its own — dropping `notes` back out loses nothing. Ship it independently
of the fix to 002.

**Go/no-go: no-go on 002 as written; 001 can ship.**
