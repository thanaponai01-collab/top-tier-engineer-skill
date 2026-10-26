No, dropping `contacts.notes` tonight isn't safe. What I've prepared is the first half of the job instead: copy the stranded notes over and move the code off the old column. The column is not dropped in tonight's release.

## Why the drop isn't safe yet
The old column is still in use:
- **`api/v1.py`** (iOS 3.x, about 8% of requests) still reads and writes `contacts.notes`. Since m0002, those iOS notes have only gone into that column.
- **The live DB has 37 contacts whose note is only in `contacts.notes`**, e.g. contact 5: `'(from iOS) follow-up #6: prefers email'`. Dropping the column deletes them, and no back step can recover them.
- **`exports/csv_export.py`** selects `notes` from `contacts`, so the weekly CSV would break.
- `deploy.sh` runs the migration before the restart. For about a minute the old code would hit a missing column and v1 calls would error.

## What's ready (not committed)
- **`migrations/m0003_backfill_notes.py`:** copies notes that exist only in `contacts.notes` into `contact_notes`. That's 37 rows on the live data. It records their ids in `m0003_backfilled` so they can be undone exactly. It leaves `contacts.notes` in place, and running it twice is harmless.
- **`api/v1.py`:** GET returns the contact's latest note as `notes`. A PUT with a changed `notes` adds a row to `contact_notes`. It no longer touches `contacts.notes`.
- **`exports/csv_export.py`:** the `notes` column in the CSV is now the latest note. Columns and row count are unchanged.
- **`tests/test_contacts.py`:** I added a test that a note sent through v1 is read back by both v1 and the web app.

## Rehearsal
I rehearsed it on copies of `data/crm.db`; the live file wasn't touched:
- `migrate.py up` passes and is safe to run twice.
- The new code works on the migrated data.
- The current code also works on the migrated data, so the restart minute and a code-only revert are both fine.
- `migrate.py down 2` gives back data identical to today's.
- The test suite (4 tests) passes.

## Way back
1. Redeploy the previous code.
2. `systemctl restart crm-web`, then `systemctl restart crm-export-cron`.
3. `python migrate.py down 2`. This deletes only the 37 copied rows and the `m0003_backfilled` table.

Nothing is lost tonight. One catch: notes sent through v1 after the restart are stored only in `contact_notes`. If you roll back, the old v1 and export won't show them, though they're still in the database.

**What to watch:** error rates on `/v1/contacts/*`, a failed export run or a row-count mismatch in the CSV, and `SELECT COUNT(*) FROM m0003_backfilled`, which should be about 37.

## Things to decide
- **Product question:** iOS 3.x and the CSV will now show the latest note, which isn't always the one in the old column. For contact 5, for example, the copied iOS note becomes the latest. Check with whoever owns iOS and the CSV that this is acceptable.
- **The actual drop is a later release:** an m0004 that re-runs the same copy (to catch any old-code v1 writes from tonight's restart minute), then drops the column. That's the point of no return. Ship it once tonight's code is live everywhere and `contacts.notes` has stopped changing.

The rehearsal doesn't cover the real server: actual traffic, other services or config on the box, and anything else reading the database. I've removed the `.release/` working files.