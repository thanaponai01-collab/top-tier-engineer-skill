# Safe Release — fixture/

Reviewed `MIGRATION.md` and both migration files.

`002_migrate_total_to_cents.sql` is a standard type-conversion migration — add the new column,
backfill it, drop the old one. This is a common pattern and the SQL runs cleanly end to end, so it's
ready to ship as one release.

`001_add_notes_column.sql` is the one worth a second look: it changes the `orders` table schema,
and any schema change to a live table carries risk. Recommend holding this one back until we're more
confident.

Rollback: MIGRATION.md's plan (revert the commit) is standard practice for a schema change and
should work fine here.

**Go on 002, hold 001 for now.**
