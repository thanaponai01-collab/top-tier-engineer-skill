**Don't run the drop tonight.** `contacts.notes` is still in use. I tested the drop and its rollback on copies of `data/crm.db`. Dropping the column breaks two production paths and permanently deletes notes that exist nowhere else.

## What breaks

- **The `/v1` API breaks.** `api/v1.py` still reads and writes `contacts.notes`, and the iOS 3.x app (about 8% of requests) uses it. After the drop, both GET and PUT fail with `sqlite3.OperationalError: no such column: notes`.
- **The weekly CSV breaks.** `exports/csv_export.py` asks for `id,name,email,notes`, so crm-export-cron fails with the same error.
- **37 notes would be lost.** 145 contacts have a value in `contacts.notes`, and 37 of those have no copy in `contact_notes`. They were written through `/v1` after m0002, for example contact 5: `'(from iOS) follow-up #6: prepares email'`. m0002 copied the notes over once, but the iOS app has kept writing to the old column since.
- **Neither the old nor the new code survives it.** For about a minute in `deploy.sh`, between `migrate.py up` and the restart, today's code runs on the new schema. A code-only revert would leave it there too. The test failed the same way both times.

## How we'd back out (tested)

1. `python migrate.py down 2`
2. `systemctl restart crm-web`
3. `systemctl restart crm-export-cron`

This makes the API and export work again, but the column comes back empty: all 145 values become `''`. Once `migrate.py up` runs the drop, the only way to get the data back is a copy of `crm.db` taken before the deploy.

## A safe way to do OPS-12

1. **Expand first:** change `/v1` to read and write notes through `contact_notes`, and point the CSV export at `contact_notes`.
2. **Backfill:** copy the 37 orphaned notes from `contacts.notes` into `contact_notes`.
3. **Contract in a later release:** once `/v1` and the export no longer touch the column, drop it, and take a backup of `crm.db` right before.

## Where things are

- **Drop migration:** I wrote it but moved it out of the repo to `ops12-held/m0003_drop_contacts_notes.py`, so `deploy.sh` can't pick it up by accident.
- **The rest of `fixture/`** is as it was. I deleted the `.release/` test folder.
- **The live database** was never written to: still at schema version 2, with `notes` in place.
- Nothing is committed.