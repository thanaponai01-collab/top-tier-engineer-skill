I haven't made any changes: it isn't safe to drop the column tonight. I didn't write a migration either, because `deploy.sh` runs `migrate.py up` on whatever files are in `migrations/`. A drop file sitting there would run tonight, committed or not.

## Why it isn't safe

**1. The column is still in use.** It isn't dead weight:
- `api/v1.py` reads `notes` from `contacts` in `get()` and writes it in `put()`. The iOS 3.x app uses this API, and it's still about 8% of requests.
- `exports/csv_export.py` selects `id,name,email,notes FROM contacts` for the weekly sales CSV.
- Only `app/contacts.py` moved to `contact_notes`.

After a drop, every v1 GET and PUT and the export cron would fail with "no such column".

**2. Dropping it would lose real data.** m0002 copied notes over once. Since then, iOS clients have kept writing to `contacts.notes` through v1, and those writes never reach `contact_notes`. I checked the live DB read-only:

| | |
|---|---|
| contacts with a non-empty `notes` | 145 / 200 |
| rows in `contact_notes` | 133 |
| **contacts whose `notes` value is missing from `contact_notes`** | **37** |

For example, contact 5 has `"(from iOS) follow-up #6: prefers email"` in `contacts.notes`, but only `"budget approved"` in `contact_notes`. Contacts 58 and 67 have no `contact_notes` rows at all. After a drop, those 37 notes would be gone for good.

**3. A "down" wouldn't help.** SQLite's `DROP COLUMN` can't be reversed. A `down()` could add the column back, but it would come back empty. And per the README, the old code keeps serving on the new schema for about a minute after the migration runs. So even a perfect code change would cause errors during deploy.

## What I'd suggest instead

Split it across separate deploys:

1. **Deploy A (code only, no drop):**
   - Point `api/v1.py` at `contact_notes`. Someone has to decide what a v1 `PUT notes` should mean: append a note, or replace the latest one. v1 GET also needs a single string, e.g. the latest note or all of them joined.
   - Point the CSV export at `contact_notes` too. The sales team should agree on the column format.
   - Add a migration that backfills the notes that exist only in `contacts.notes`. That's the 37 today, and the query has to run again at deploy time, since iOS keeps writing.
   - Add tests so v1 and the export no longer touch `contacts.notes`.
2. **Check:** after a while, confirm nothing writes to `contacts.notes` anymore and the counts match.
3. **Deploy B:** add `m0003` to drop the column. Take a backup right before it, e.g. `sqlite3 data/crm.db ".backup crm-pre-m0003.db"`. That backup is the only real way to back out.

**Backing out:**
- Deploy A is safe to revert: put the old code back, and the backfilled rows in `contact_notes` do no harm.
- After Deploy B, backing out means stopping the services and restoring the backup file. Anything written after the backup would be lost, so keep the window short.

I can write Deploy A now if you tell me which v1 `PUT notes` behaviour and CSV format you want. I'd move OPS-12 off tonight's deploy.