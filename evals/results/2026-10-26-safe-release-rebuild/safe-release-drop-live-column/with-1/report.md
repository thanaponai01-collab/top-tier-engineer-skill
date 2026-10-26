**Don't ship this tonight.** `contacts.notes` is still in use, so dropping it would break production and lose notes.

## What I found
I tested the drop on copies of `data/crm.db`, running both today's code and the changed code. The live database wasn't touched: it's still at version 2, the `notes` column is still there, and `contact_notes` still has 133 rows.

1. **Two parts of the code still use the column.**
   - `api/v1.py` reads and writes `contacts.notes`. This is the API the iOS 3.x app uses, about 8% of requests.
   - `exports/csv_export.py` (the weekly sales CSV) reads it.
   - After the drop, both fail with `no such column: notes`. Restarting services doesn't fix that, because the new code reads the column too.
2. **37 contacts have notes that exist only in that column.** The iOS app wrote them through v1 after m0002 copied notes over, for example contact 5: `(from iOS) follow-up #6: prefers email`. A plain `DROP COLUMN` would delete them for good.
3. **The way back works.** `python migrate.py down 2` puts the column back and fills it from `contact_notes`. In the test, every row came back with its original value and today's code passed all checks again. The 37 copied notes stay in `contact_notes` afterwards (rows with id > 133), so nothing is lost.

## What I left you
- **`fixture/OPS-12_m0003_drop_contacts_notes.py.draft`**: the draft migration. It first copies the 37 notes into `contact_notes`, then drops the column. I moved it out of `migrations/` on purpose. Right now `migrations/` contains only m0001 and m0002, so if you run `deploy.sh` tonight from this folder, it won't change the schema.
- Nothing is committed. I deleted the `.release/` test folder.

## To make OPS-12 safe, do it in two releases
1. **Release A, code only:** change `v1.get` and `v1.put` to read and write `contact_notes` (when an iOS client PUTs `notes`, add it as a new note), and change the CSV export to read `contact_notes`. Run the copy step from the draft once to bring the 37 notes over. The column stays.
2. **Release B, after every server and the export cron run Release A:** apply the draft as `migrations/m0003_*.py`. Nothing reads the column any more, so the drop is safe.

You'll need to decide how a single v1 `notes` string should map to a list of notes; I didn't guess at that.

**If someone does run the drop**, back out with `python migrate.py down 2`, then `systemctl restart crm-web` and `systemctl restart crm-export-cron`. Every iOS notes edit made between the drop and the back-out fails and is not saved. Watch for 5xx errors on `/v1/contacts/*` and for failures in the export cron.