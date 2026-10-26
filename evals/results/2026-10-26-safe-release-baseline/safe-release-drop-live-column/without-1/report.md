I stopped short of writing the migration. **It isn't safe to drop `contacts.notes` tonight.** The column is still in use, and the live database has notes that exist only there.

**What I found**

- **37 contacts have notes that exist nowhere but `contacts.notes`.** I checked a copy of `data/crm.db` (schema version 2, 200 contacts, 133 rows in `contact_notes`). Examples: contact 5 "(from iOS) follow-up #6: prefers email", contact 9 "(from iOS) follow-up #35: renewal in Q1". m0002 copied notes over only once. Anything written after that went to the old column and nowhere else. Dropping the column would delete those notes for good.
- **The v1 API still reads and writes the column.** In `api/v1.py:11` and `api/v1.py:17-22`, `GET` and `PUT /v1/contacts/<id>` use `contacts.notes`. Its docstring says it's kept for iOS 3.x (about 8% of requests), which is where the "(from iOS)" notes come from. After a drop, both endpoints would fail.
- **The weekly sales CSV reads it too.** `exports/csv_export.py:7` has `notes` in `FIELDS`, so `crm-export-cron` would fail.
- **The tests miss all of this.** `test_v1_update` and `test_export` run against a fresh database where the column exists.
- **The deploy has a gap.** Per the README, `deploy.sh` migrates first and restarts services about a minute later. Even with the code fixed, the old code would be querying a dropped column during that minute.

**Backing out**

`migrate.py down` couldn't undo this. A drop migration's `down()` can add the column back, but not the 37 notes. Rolling back would mean restoring a copy of `crm.db` taken just before the deploy, and losing any writes made after that point.

**Safer plan: split it across two deploys**

1. **Deploy A (could go tonight):**
   - Add a migration that copies the 37 notes into `contact_notes`.
   - Change `api/v1.py` to read and write notes through `contact_notes`, and point the CSV export at it.
   - Add tests that would fail if anything still touches `contacts.notes`.
   - Leave the column in place, so the old code keeps working during the restart gap.
   - To back out: revert the code. The column is still there, so nothing is lost.
2. **Deploy B (a later cycle):** once nothing writes to `contacts.notes`, copy over anything written to it during the restart gap, then drop it. Take a file backup first.

Before I write Deploy A, you need to make one call. v1 returns a single `notes` string, but `contact_notes` holds several notes per contact. What should iOS 3.x get?
- On `GET`: the latest note, or all of them joined together?
- On `PUT`: add a new note, or replace the existing ones?

I haven't changed anything in `fixture/`, so tonight's `deploy.sh` would apply no migrations. The only thing I created is the database copy at `/tmp/ops12/crm-copy.db`. Tell me how v1 should behave and I'll prepare Deploy A.