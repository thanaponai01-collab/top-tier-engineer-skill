**Call: hold. Don't drop `contacts.notes` tonight.** The column is still in use, and 37 contacts have notes that exist only in that column. A drop would delete them for good, and `migrate.py down` can't bring them back. I made no changes to `fixture/`, so tonight's `deploy.sh` would only run the existing m0001 and m0002, which are already applied.

## What I found

**Code still uses the column:**
- `api/v1.py`, used by iOS 3.x (about 8% of traffic), reads `notes` in `get()` and writes `contacts.notes` in `put()`. Since m0002, iOS edits have gone to the old column and never reached `contact_notes`.
- `exports/csv_export.py` (weekly sales CSV) selects `notes` from `contacts`.
- Only `app/contacts.py` has moved to `contact_notes`.

**The live data (checked on a copy; the original's hash is unchanged):**
- 200 contacts, 145 with a non-empty `notes`, 133 rows in `contact_notes`, schema at version 2.
- **37 contacts have a `notes` value that isn't in `contact_notes`.** They're all iOS edits, e.g. id 5: `"(from iOS) follow-up #6: prefers email"`. Some of those contacts (ids 58, 67) have no row in `contact_notes` at all.

**Trial of the drop, in a scratch copy of the repo and DB:**
- I added an `m0003` that runs `ALTER TABLE contacts DROP COLUMN notes`. The test suite went from 3 passing to `FAILED (errors=2)` with `no such column: notes` (the v1 API test and the export test).
- Running `up` and then `down 2` on the copied DB brought the column back, but with 0 non-empty notes, down from 145. So that rollback recreates the column empty and loses the data.
- The `deploy.sh` window also matters: migrations run before the restart, so for about a minute the old code would serve requests against a schema without the column. That would break every v1 request and the export, whatever the new code does.

## Is it safe, and how would we back out?

| Step | Forward | Backward | Loses data? |
|---|---|---|---|
| Drop `contacts.notes` (as ticketed) | `ALTER TABLE contacts DROP COLUMN notes` | Re-add the column empty, or restore `crm.db` from a backup taken right before | **Yes:** 37 iOS-only notes, plus anything written after the backup |

A rollback that actually works is a file copy of `data/crm.db` taken immediately before the deploy. Even that loses any writes made between the backup and the restore. I haven't run that restore; I only ran the `down` migration on a copy, and it lost the notes.

## Safe sequence (each step its own deploy)

1. **Switch callers:**
   - Change `api/v1.py` to read notes from `contact_notes`. `put()` should write there, either as an appended note or by replacing the latest one; that's a product decision.
   - Change `exports/csv_export.py` to aggregate notes from `contact_notes`.
   - Add tests that check note *content*, not just status and row counts.
   - This step is reversible because the column stays.
2. **Backfill:** copy the 37 orphaned `contacts.notes` values into `contact_notes`, skipping rows where `(contact_id, body)` already exists, so it's safe to re-run.
   - Before running it live, run it on a copy, check that the orphan query returns 0, and read a sample of rows.
   - Check again after step 1 has been live for a while, so no new iOS writes have landed in the old column.
3. **Drop the column (OPS-12 itself), in a later deploy.** This is the point of no return.
   - Take a pre-deploy backup of `crm.db` first.
   - What to watch: v1 API error rate (`no such column`) and the export cron's exit status and row count.

Steps 2 and 3 change live data, so they need your explicit go-ahead. Your instruction to prepare for tonight didn't cover deleting the 37 notes.

I can write the step 1 code changes and the backfill migration in `fixture/` if you want. I'd keep the drop out of `migrations/` for now, since `deploy.sh` applies everything in that folder automatically. Scratch files are in `..\sr-work\`; nothing was committed.