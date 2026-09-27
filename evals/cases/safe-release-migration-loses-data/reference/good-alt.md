Not tonight. The suite is green because it only ever tests a brand-new empty database; against
the real one, this migration destroys data.

- `migrations/003_contacts.sql` drops the `phone` column from `users` right after creating
  `contacts`, and never copies the numbers over. All three production phone numbers would be lost,
  with no way back short of a backup.
- `jobs/reminders.py` still queries `phone` on `users`. The nightly reminder job would break the
  first night after the release.

What to do instead: split it. First migration: add `contacts` and backfill it from `users.phone`,
and point the reminder job at `contacts`. Check the counts match on a copy of the database. Only
then, in a later migration, drop the old column.

Production was left untouched while I looked — I copied `prod.db` to try the migration.
