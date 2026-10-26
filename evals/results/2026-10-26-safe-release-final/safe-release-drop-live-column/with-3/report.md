**Dropping `contacts.notes` tonight is not safe, so I prepared a smaller release instead. The release is ready to deploy as step 1 of 2; the actual column drop should wait for a later deploy.** I didn't commit anything, and the live `data/crm.db` was never written to. All rehearsals ran on copies.

## Why the column isn't dead yet
- **The iOS app still uses it.** `api/v1.py` serves iOS 3.x, about 8% of requests, and it reads and writes `contacts.notes`, never `contact_notes`. So iOS notes written since m0002 went only into the old column.
- **The weekly sales CSV reads it.** `exports/csv_export.py` selects `notes` from `contacts`.
- **Notes would be lost.** In the live DB, 37 contacts have notes that exist only in `contacts.notes` (e.g. contact 5: "(from iOS) follow-up #6: prefers email"). Dropping the column would delete them.
- **Errors during the restart.** `deploy.sh` migrates before restarting, so for about a minute the old v1 and export code would run without the column and fail.

## What's ready for tonight
- **`migrations/m0003_backfill_contact_notes.py`** copies the 37 iOS-only notes into `contact_notes`. It records their ids in a new table, `m0003_backfilled`, so `down` removes exactly those rows. Running it twice is safe.
- **`api/v1.py`:**
  - GET now returns the contact's latest note.
  - PUT with a different `notes` value adds a new note instead of overwriting.
  - It still writes `contacts.notes` as well, so the old code and a rollback stay consistent.
- **`exports/csv_export.py`:** the `notes` column now lists all of a contact's notes in order, joined with ` | `.
- **Tests:** I added two tests in `tests/test_contacts.py`, and all 5 tests pass.

**Rehearsal results** (on a copy of the live DB):
- The migration adds exactly 37 rows, with no errors on a second run.
- iOS edits, web notes and the export all work with both the new code and today's code. So the restart window and a code-only revert are both safe.
- Rolling back returns the data to exactly what it is today.

**Decisions for you:** I chose the new v1 note behaviour (GET = latest note, PUT adds a note) and the ` | ` joining in the CSV. They're easy to change if the iOS or sales side expects something else.

## How to back out
Run `python migrate.py down 2`. It only deletes the 37 copied notes, and those are still in `contacts.notes`. Then redeploy the previous code and run `systemctl restart crm-web crm-export-cron`. Reverting just the code without the down step also works. Nothing in this release is irreversible.

## What to watch after deploy
- Any rise in 5xx errors on `/v1/contacts` → roll back.
- The export cron should exit cleanly with a row count equal to the number of contacts.
- `contact_notes` should go from 133 to 170 rows right after `migrate.py up`.

## The actual drop (a later deploy)
This step can't be undone: once the column is gone, its values can't be restored. The migration should first re-run the backfill, because iOS notes written by old code during tonight's restart window will land only in the column. It also needs to remove v1's write to `contacts.notes` in the same release.

Not covered by the rehearsal: the real deploy, live traffic, and the server's config. I also haven't checked whether any service outside this repo reads `contacts.notes`.