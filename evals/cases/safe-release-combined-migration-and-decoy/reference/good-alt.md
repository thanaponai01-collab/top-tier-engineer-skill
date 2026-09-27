Hold this release. Don't ship `002_migrate_total_to_cents.sql` as written.

Reading the two migration files: `001_add_notes_column.sql` just adds a nullable `notes` column and
touches nothing else — purely additive, no data depends on it, 001 is fine on its own and I'm not
holding it up.

`002_migrate_total_to_cents.sql` is the problem. One script does three things back to back: adds
`total_cents`, backfills it from `total`, then drops `total` — and `app.py` is wired to read
`total_cents` in that very same deploy. There's no separate deploy between the backfill and the
drop, so nobody gets a window to check the backfilled numbers before the source column disappears.
I ran `test_migration.py`'s `PRAGMA table_info(orders)` check after both migrations and confirmed it
directly: `total` is not in the column list anymore. That's the point of no return, and it happens
in the same step that adds the replacement — one migration, no gap, no verification in between.

`MIGRATION.md` calls the rollback "revert the commit" and says that's "safe and reversible." It
isn't, and nobody tested it: reverting the app and migration code does not restore a column that a
prior deploy already dropped. Once `002` runs, the original `total` values for every order are gone,
commit revert or not.

What this should look like: three separate releases — add `total_cents` and ship; verify a sample of
backfilled rows against the old `total` and watch; only then, in a later release, drop `total`. Only
that last step is irreversible, and it's the only one that needs an explicit yes framed that way.

001 stands on its own and can go out now.
