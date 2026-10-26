I read all four files in `fixture/app/`. Here's how I'd structure it, plus a few things to settle before anyone writes code.

## What's there now

- `db.py`: one `execute()` helper. Each call opens its own SQLite connection, commits and closes. There's no transaction you can span across two calls.
- `reports/models.py`: `list_reports(owner_id)` and `get_report(report_id)`.
- `reports/views.py`: list and detail views. `render()` is a stub that just returns the data.
- `users/models.py`: `find_user`. The export doesn't need it.
- There's no schema or migration file anywhere. The `reports` and `users` tables are created somewhere outside this folder.

## Fix this first

**`get_report` doesn't check who owns the report.** `report_detail` gets whatever `report_id` it's given, so any user can read any report. If the CSV export reuses that path, anyone could download anyone's report. Before or alongside the export work, add an owner check: either `get_report(report_id, owner_id)` with `AND owner_id = ?`, or a check in the view. That also fixes the detail page.

## Proposed structure

Everything stays inside `app/reports/`, because the history is about reports.

**1. New table `report_exports`**
```
id           INTEGER PRIMARY KEY
user_id      INTEGER NOT NULL
report_id    INTEGER NOT NULL
report_title TEXT    NOT NULL   -- copied at export time
exported_at  TEXT    NOT NULL   -- UTC ISO-8601
INDEX (user_id, exported_at DESC)
```
Copy the title into the row rather than looking it up from `reports`. That way the history still reads correctly if the report is renamed or deleted, and listing it needs no join. Keep `report_id` too, so a "download again" link is easy to add later.

**2. `reports/models.py`: two new functions, both using `execute()`**
- `record_export(user_id, report_id, title)`
- `recent_exports(user_id, limit=5)`, which does `ORDER BY exported_at DESC LIMIT ?`

To keep only "the last few", limit on read rather than deleting old rows. It's simpler, and you keep an audit trail. Add pruning only if the table actually grows too big.

**3. New `reports/export.py`: building the CSV, with no database or request code**
- `report_to_csv(report) -> str` using the `csv` module. It's a pure function, so it's easy to unit test.
- Protect against CSV formula injection: if a cell starts with `=`, `+`, `-`, `@`, tab or carriage return, put a `'` in front. Report titles and bodies are user-entered, and this file will be opened in Excel.

**4. `reports/views.py`: new `report_export_csv(request, report_id)`**
1. Fetch the report with the owner check (return 404 if it's not the user's).
2. Build the CSV.
3. Call `record_export(...)` only after the CSV built successfully.
4. Return it with `Content-Type: text/csv` and `Content-Disposition: attachment; filename="..."`. Clean the filename, because it comes from the title.

Then pass `recent_exports(request.user_id)` into `report_list` so the reports page can show the history.

## Questions to answer first

1. **What goes in the CSV?** A report has only `id, title, created_at, body`. Is the export that one row, or is `body` structured data (JSON or a table) that should be split into rows and columns? This is the biggest unknown, and it decides what `export.py` looks like.
2. **What's the response layer?** `render()` returns raw data and can't set headers. Someone needs to say which framework sits underneath, or that layer needs a way to return a response with content type and headers.
3. **Where do schema changes go?** There are no migrations in `fixture/`, so the `report_exports` table needs a home.
4. **Timestamp format:** check how `reports.created_at` is stored and use the same format for `exported_at`. UTC ISO-8601 is my default.
5. **Single report or the whole list?** "Download as CSV" on the reports page could mean exporting the list. If so, the history's `report_id`/`report_title` columns would need to allow "all reports".