# Release plan

This release ships two migrations plus the app change that reads the new column:

1. `001_add_notes_column.sql` — adds a free-text `notes` column to `orders`.
2. `002_migrate_total_to_cents.sql` — moves `orders.total` (dollars) to `orders.total_cents`
   (integer cents), and `app.py` is updated in the same deploy to read `total_cents`.

**Rollback:** revert the commit. Both migrations are schema changes, so this is safe and
reversible like any other code change.
