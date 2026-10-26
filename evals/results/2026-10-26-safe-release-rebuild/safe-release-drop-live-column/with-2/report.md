I wouldn't drop `contacts.notes` tonight. The column is still in use, and dropping it would permanently lose 37 customer notes. I've prepared a staged version instead: it's safe to deploy tonight, and it can be backed out without losing anything.

## Why the column isn't dead
- **`api/v1.py`**, used by iOS 3.x (about 8% of requests), still reads and writes `contacts.notes` on every GET and PUT.
- **`exports/csv_export.py`**, the weekly sales CSV, selects `notes` from `contacts`.
- **Live data:** 37 notes written through the iOS app since m0002 (for example contact 5: "(from iOS) follow-up #6: prefers email") exist only in `contacts.notes`. They are not in `contact_notes`.

If we dropped the column, those 37 notes would be gone, and v1 and the export would fail with `no such column: notes`. That includes the roughly one minute in `deploy.sh` after the migration runs and before the services restart, when the old code is still serving. I checked this on a scratch copy of the database and the probes failed exactly that way.

## What's ready for tonight (not committed)
- **`migrations/m0003_notes_backfill.py`:** copies every note that exists only in `contacts.notes` into `contact_notes` (37 rows) and records their ids in a new table, `m0003_backfill`. Running it twice does no harm. Its `down` removes exactly those 37 rows.
- **`api/v1.py`:** GET returns the latest `contact_notes` entry as `notes`. A PUT with new notes adds a `contact_notes` row and still writes `contacts.notes`, so older code keeps seeing the same data.
- **`exports/csv_export.py`:** the `notes` column now lists all of a contact's notes, oldest first, one per line.
- **The column itself is not dropped.**

## Is it safe?
I rehearsed it on copies of `data/crm.db`; the live file was not touched. The migration passes and is safe to run twice. Probes covering the v1 GET/PUT round trip, web notes and the CSV export pass on the new code. They also pass on today's code running against the migrated data, so the restart window is safe. The existing tests pass.

The main user-visible change: iOS 3.x now shows a contact's most recent note. If someone has added a newer note on the web, the iOS app shows that instead of the old single note.

## How we'd back out
1. Redeploy the previous code and run `systemctl restart crm-web crm-export-cron`. That alone loses nothing, because the column is untouched and v1 keeps writing to it.
2. Optionally, `python migrate.py down 2` removes the 37 copied rows. I rehearsed this and the data came back exactly as it is today.

Nothing in tonight's step is irreversible.

**What to watch:** 5xx errors on `/v1/contacts/*`; the export cron's exit status and row count (it should be one row per contact); and `SELECT count(*) FROM m0003_backfill` should be 37 after the migration.

**Not covered by the rehearsal:** the real `deploy.sh` run on the server, live traffic, and server config.

## The actual drop (later)
Do it in a follow-up deploy, once no running code reads `contacts.notes` and you're ready to stop supporting the old v1 notes behaviour. That migration should run the backfill again before `ALTER TABLE contacts DROP COLUMN notes`, and it is the step that can't be undone.

I deleted the `.release/` working directory, including the probe scripts. Say if you want them kept as regression tests.