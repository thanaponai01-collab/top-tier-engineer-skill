**Verdict: clean, with one gap to fix.** `fixture/` is 4 small files with one DB owner (`app/db.py:11`) and dependencies pointing one way (views → models → db). I chose **Design new**. This is an addition inside the existing `reports` module, so nothing needs replacing. The gap is that there is no ownership check on single-report reads. I read all 4 files (*traced*).

## What's already there
- **DB access:** `app/db.py:11` `execute()` is the only DB path. Use it for the history too, and don't add a second store.
- **Report queries:** `app/reports/models.py:4,10` own the report queries. The history queries belong beside them, because they change for the same reason (the `reports` tables).
- **Gap:** `get_report(report_id)` (`models.py:10`, called at `views.py:10`) has no `owner_id` filter. Any user who knows an id can read that report. An export built on it would leak CSVs, so scope the export by owner.
- **Nothing to reuse for CSV:** there's no CSV code, no routing and no real response type. `render()` (`views.py:14`) is a stub. Nothing in the fixture shows how views are wired to a framework or how the schema is created. I couldn't check either, so the file response and the table creation below are assumptions to confirm.

## Open question for product
"Reports page" could mean **(a)** the list at `report_list`, exported as one CSV of all rows, or **(b)** a single report's content. The history entry "report title" only makes sense for (b), or for (a) with a fixed title like "All reports". I'd assume (b), one export per report, because `title` and `body` exist on a single report (`models.py:11`). Please confirm before building.

## Structure
1. **`reports/csv_export.py`** is pure: `to_csv(report_row) -> str`, with no DB, clock or HTTP.
   - Use stdlib `csv`, which is about 10 lines, so no dependency.
   - Prefix cells starting with `= + - @` with `'` to prevent spreadsheet formula injection. Titles are user-controlled.
2. **`reports/models.py`** gets three additions:
   - `get_report(report_id, owner_id)` adds the ownership filter. Update the one existing caller at `views.py:10`.
   - `record_export(owner_id, report_id, title)`
   - `recent_exports(owner_id, limit=5)`
3. **`reports/views.py`** gets `report_export(request, report_id)`:
   - fetch the report scoped to the owner, and return not-found if it's missing
   - build the CSV
   - call `record_export`
   - return the file response
   - the history list is added to the data `report_list` returns (`views.py:5`), so the page needs no new endpoint
4. The button is a link to the export route. No JS is needed.

**Who may call whom:** views → csv_export and models; models → db. `csv_export` imports nothing.

**Errors:** a missing or foreign report gives the same not-found response, so ids can't be probed. If `record_export` fails, the download still succeeds and the failure is logged. History is secondary to the file.

## Decisions
**History storage (one-way door: a stored data shape).**
- **Option A, recommended:** a new table `report_exports(id, owner_id, report_id, title, exported_at)`. It stores a title snapshot, so the history still reads correctly after a rename or delete. It costs one table to create and back up, and it needs a migration. I couldn't find where the schema lives.
- **Option B, simplest:** `report_id` and `exported_at` only, with the title joined live. It's narrower, but a deleted report breaks the history row, and a renamed one shows the new title instead of the one exported.
- Whichever you pick, add an index on `(owner_id, exported_at)`. Confirm where schema changes live before writing this.

**"Last few" (two-way, a one-line decision):** `ORDER BY exported_at DESC LIMIT 5` as a constant. Don't delete old rows at launch, so you keep an audit trail and can change N freely.

**Time (two-way):** store UTC ISO text and format it on display.

**CSV generation (two-way):** generate it synchronously per request. That's fine for one report. If report bodies get large, stream it later. Nothing needs designing now.

## Pre-mortem
1. **Cross-user leak.** An export built on the unscoped `get_report`. *Change:* the owner filter above, plus a test that user B gets not-found on user A's id.
2. **Formula injection in Excel.** Fixed in `csv_export` with a test on a title like `=HYPERLINK(...)`.
3. **History drift.** Title/id mismatch after renames or deletes, or a history write that blocks the download. Fixed by the title snapshot (Option A) and the non-fatal write.

## Order of moves
Each step lands alone:
1. Add the owner filter to `get_report` and update its caller. *Proof:* a cross-owner read returns None.
2. Add `csv_export.py` with unit tests: quoting, commas, newlines, `=` prefix.
3. Add the table, `record_export` and `recent_exports`. *Proof:* record 7, read back 5, newest first, scoped per owner.
4. Add the `report_export` view and the button. *Proof:* download a file, then see a history row. A foreign id gives not-found and writes no row.
5. Show the history on the page.

No code or files have been written.