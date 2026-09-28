I read all four files in `fixture/app/`: `db.py`, `users/models.py`, `reports/models.py` and `reports/views.py`. It's a small codebase with a clear pattern: all SQL goes through `db.execute`, each feature has a `models.py` of query functions, and views call those. The export feature fits that pattern without any new infrastructure. There is one existing bug you should fix first, though.

## Fix first: report detail doesn't check who owns the report

`get_report(report_id)` (`app/reports/models.py:10`) filters only on `id`, and `report_detail` (`app/reports/views.py:9`) passes the ID straight from the URL. `report_list` filters by `owner_id`, but the detail view doesn't, so any user can load any report by guessing its ID. A CSV export built the obvious way (`get_report(report_id)` → serialize) would carry the same hole, and would hand out the data as a file.

**Recommendation:** add an owner check, either `get_report(report_id, owner_id)` with `AND owner_id = ?`, or a separate `get_report_for_user`. Use it in both `report_detail` and the new export view. This is a small change, but do it before export, not alongside it.

## Proposed structure

**1. Data: a new `report_exports` table**
```
report_exports(
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL,   -- who exported
  report_id   INTEGER,            -- kept for linking; may point at a deleted report
  title       TEXT NOT NULL,      -- title as it was at export time
  exported_at TEXT NOT NULL       -- UTC ISO-8601
)
INDEX ON (user_id, exported_at DESC)
```
- **Save a copy of the title** instead of joining back to `reports`. That way the history still reads correctly if a report is later renamed or deleted, and it matches what product asked for: "a timestamp and the report title."
- The fixture has no schema or migration files, so we need to find out where the `users` and `reports` tables are defined and add this table there.

**2. Queries: add to `app/reports/models.py`**
- `record_export(user_id, report_id, title)` does one `INSERT`.
- `recent_exports(user_id, limit=5)` does `ORDER BY exported_at DESC LIMIT ?`.
- For "last few", limit the rows when reading them. Pruning old rows can wait; it's easy to add later if the table grows.

**3. CSV generation: new `app/reports/export.py`**
- A pure function `report_to_csv(report) -> str` that uses the `csv` module and does no database calls or request handling, so it's easy to unit-test.
- **Protect against spreadsheet formula injection.** If a user-controlled cell starts with `=`, `+`, `-`, `@`, tab or CR, prefix it with `'`. Otherwise a report title like `=HYPERLINK(...)` runs as a formula when someone opens the file in Excel.

**4. Views: `app/reports/views.py`**
- `report_export_csv(request, report_id)`:
  1. Load the report with the owner-checked query (404 if it's missing or belongs to someone else).
  2. Build the CSV.
  3. `record_export(...)`, only after the CSV was built successfully.
  4. Return it with `Content-Type: text/csv` and `Content-Disposition: attachment; filename="..."`.
- `report_list` also passes `recent_exports(request.user_id)` so the page can show the history next to the list.
- **Gap:** `render()` is a stub that returns data unchanged, and the fixture has no response object or routing. Someone needs to confirm how the real app sets headers and returns a file download.

## Questions for product before anyone writes code

1. **What goes in the CSV?** A report has one `body` field. Is the body already tabular data, or should the export be the report *list* (`id, title, created_at`)? This decides everything in step 3.
2. **Per-report button or whole-list export?** The schema above assumes one report per export. A list export would make `report_id` nullable and need a generated title, such as "All reports".
3. **How many is "last few"?** I've assumed 5.
4. **Should exports of deleted reports still show in the history?** Saving a copy of the title makes that work by default.

## Suggested order of work
1. Owner check on `get_report`, with a test that user B can't load user A's report.
2. Migration for `report_exports`, plus `record_export` and `recent_exports`.
3. `export.py`, with tests for escaping and formula injection.
4. Export view and history on the list page.