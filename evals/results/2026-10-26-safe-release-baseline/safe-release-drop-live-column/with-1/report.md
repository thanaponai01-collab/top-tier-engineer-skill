**It's not safe to drop the column tonight. If we do, 37 customer notes are gone for good and two live features start failing.** `contacts.notes` is still in use. The move to `contact_notes` in m0002 was only half done. The web app switched over, but the old v1 API (iOS 3.x, about 8% of requests) and the weekly CSV export never did. The v1 API has kept writing notes into the old column ever since.

I didn't add a migration to `fixture/`, so tonight's `deploy.sh` won't touch this column. I made no changes to the repo or `data/crm.db` (its checksum still matches the copy I took) and committed nothing.

## What I found

I worked on a copy of the live database.

- **The data has drifted apart.** 200 contacts, 145 with a non-empty `notes`, and 133 rows in `contact_notes`. **37 contacts have notes that exist only in the old column.** They're all newer iOS notes, like `(from iOS) follow-up #6: prefers email` on contact 5. One contact (58) has no row in `contact_notes` at all.
- **Code that still uses the column:**
  - `api/v1.py` `get` and `put` read and write `contacts.notes` directly.
  - `exports/csv_export.py` exports `id,name,email,notes` from `contacts`.
  - `app/contacts.py` is the only part that has fully moved to `contact_notes`.

## Trial run on a scratch copy

I wrote the obvious one-step migration (`ALTER TABLE contacts DROP COLUMN notes`) and ran it against a copy of the code and data:

- The tests went from 3 passing to 2 errors (`test_v1_update`, `test_export`), both `no such column: notes`.
- `GET /v1/contacts/5`, `PUT /v1/contacts/5` and the CSV export all failed with the same error.
- **Undoing it doesn't bring the notes back.** `migrate.py down 2` re-adds the column, but every value is blank: 145 notes are wiped, and the 37 that exist nowhere else are lost. The only real way back is restoring a copy of `crm.db` taken before the deploy.
- Timing makes it worse: `deploy.sh` runs the migration before restarting the services, so the old code would be failing against the new schema for about a minute even if everything else were fixed.

## Safe order

| Step | Change | How to undo it | Data lost if undone? |
|---|---|---|---|
| 1. Copy the missing notes | A migration that copies any `contacts.notes` value not already in `contact_notes`, and is safe to re-run | Delete the copied rows (tag them) | No |
| 2. Move the callers | v1 `put` writes to `contact_notes` (and to `notes` too, for now); v1 `get` and the CSV read from `contact_notes`; run step 1 again to catch stragglers | Revert the code | No |
| 3. Watch | Confirm no new values appear only in `contacts.notes`, and watch v1 and export error rates | Revert the code | No |
| 4. Drop the column (a later, separate deploy) | `DROP COLUMN notes`, after a fresh backup of `crm.db` | Restore that backup | **Yes, from here on**: anything written to `notes` after the backup |

I haven't written steps 1 and 2. You need to decide one thing first: v1 returns `notes` as a single string, but a contact can now have several notes. Should v1 return the latest note, or all of them joined together, and should a v1 PUT add a new note or replace the latest one? The iOS 3.x app depends on this. Tell me which and I'll write steps 1 and 2 and test them on a copy.

## Rollback plan, whenever the drop does happen

1. Stop `crm-web` and `crm-export-cron`.
2. Copy `crm.db` aside right before running the migration.
3. To back out, put that copy back and deploy the previous code.

`migrate.py down` is not a real rollback here: it restores the column but not the data. Separately, m0002's `down` deletes the whole `contact_notes` table, so never run `down 1` on the live database.

My scratch files (the database copy, the inspection script and the trial-run tree) are in `%TEMP%\scratch-ops12`, outside the repo.