## Hold: dropping `contacts.notes` tonight is not safe

`contacts.notes` is still in use. Dropping it tonight would permanently delete customer notes and break the iOS app.

- **Data loss:** 37 of the 200 live contacts have a note that exists only in `contacts.notes`. All of them start with `(from iOS) follow-up …`. The iOS 3.x app (about 8% of requests) goes through `api/v1.py`, which has kept reading and writing `contacts.notes` since m0002. Those notes never reached `contact_notes`. The drop is the point where they're lost, and `migrate.py down` can't bring them back.
- **Breakage:** two callers still read the column. `api/v1.py` uses it in both `get` and `put`, and `exports/csv_export.py` (the weekly sales CSV) selects it. Dropping the column on a copy of the DB made the current v1 code fail with `no such column: notes`. Even with fixed code, `deploy.sh` migrates before restarting, so the old code would fail for about a minute.
- **Reach:** `deploy.sh` goes to 100% at once, with no canary or feature flag.

Tonight's `deploy.sh` would ship nothing new anyway, because `fixture/` has no new migration in it. I left `fixture/` and `data/crm.db` unchanged (the live DB checksum matches the copy I worked from). Nothing is committed.

## Recommended sequence

| Step | Forward | Backward | Data lost from here? |
|---|---|---|---|
| A (can go tonight once you approve it) | Add `m0003`, which copies the 37 notes that only exist in `contacts.notes` into `contact_notes` and is safe to re-run. Switch v1 and the export to `contact_notes`. | Revert the code, then `python migrate.py down 2`. `m0003` leaves `contacts.notes` untouched. | No |
| B (a later, separate deploy, after A has run cleanly for a while) | `m0004`: `ALTER TABLE contacts DROP COLUMN notes` | `python migrate.py down 3` re-adds the column and fills it with each contact's latest note. | **Yes.** Only the latest note per contact comes back. Take a backup first. |

How v1 behaves after step A: `GET` returns the contact's latest note, and a `PUT` with a changed `notes` adds a new note instead of overwriting. Please confirm that's what you want for iOS 3.x.

## What I tested (on copies of `crm.db`)

- **Tests:** all three pass on the proposed code.
- **Step A:** `migrate.py up` applied `m0003`. `contact_notes` went from 133 to 170 rows and no notes were left only in `contacts.notes`. Running it a second time added nothing.
  - v1 `GET 5` returns the iOS note, and the web app shows both of that contact's notes.
  - A v1 `PUT` lands in `contact_notes`, and the export still writes 200 rows.
- **Step A rollback:** `down 2` brought it back to version 2.
- **Step B:** after the drop, the new code works and the old code fails.
- **Step B rollback:** `down 3` put the column back, and the old v1 code returned contact 9's iOS note.

I didn't test against the real server or its SQLite version. `DROP COLUMN` needs SQLite 3.35 or newer; mine is 3.49.

## Where the proposed files are

They're in `scratch/proposal/`:
- `migrations/m0003_backfill_v1_notes.py`
- `api/v1.py`
- `exports/csv_export.py`

The step B migration is held back on purpose in `scratch/later/m0004_drop_contacts_notes.py`. If it sat in `migrations/`, `deploy.sh` would run it.

## Signals to watch after each deploy

- 5xx rate on `/v1/contacts/*`, split out from total traffic
- `crm-export-cron` succeeding and writing the full row count (200 today)
- A daily check that `SELECT count(*) FROM contacts c WHERE notes != '' AND NOT EXISTS (SELECT 1 FROM contact_notes n WHERE n.contact_id = c.id AND n.body = c.notes)` stays at 0, before step B

**Before you run anything:** I need your go-ahead to move the step A files into `fixture/`. It writes to the live DB, so take `cp data/crm.db data/crm.db.pre-ops12` first. Step B should get its own sign-off later, with a fresh backup.

**Rollback in one sentence:** for step A, revert the code and run `python migrate.py down 2` (tested, loses nothing); for step B, run `python migrate.py down 3` (tested), and restore any lost notes from the pre-drop backup.