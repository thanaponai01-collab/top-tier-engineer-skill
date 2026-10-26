I read all four files in `fixture/`. The codebase is small and consistent, so the plan below mostly follows its existing patterns. One existing bug needs fixing first, and a few questions need product answers before anyone writes code.

## What's there now

- **`app/db.py`**: every query goes through `execute()`, which opens a connection, commits and closes it each time. It returns plain tuples, with no column names.
- **`app/reports/models.py`**: has `list_reports(owner_id)` and `get_report(report_id)`. Reports have the columns `id, title, created_at, body`.
- **`app/reports/views.py`**: `render()` is a stub that returns its input. There's no routing, no response object and no way to set HTTP headers in the code I was given.
- There's no schema or migrations folder, so I can't see where tables get created.

## Fix this first: `report_detail` doesn't check ownership

`report_detail` (`app/reports/views.py:9`) fetches any report by id and never compares it to `request.user_id`. `report_list` does filter by owner, but the detail view doesn't. An export endpoint copied from the detail view would let any logged-in user download any report as a CSV just by changing the id.

Recommendation: add an owner-scoped lookup, e.g. `get_report_for_owner(report_id, owner_id)` with `WHERE id = ? AND owner_id = ?`. Use it for both the detail view and the export, and return a 404 on a miss rather than a 403, so the response doesn't reveal which ids exist.

## Proposed structure

Keep everything in `app/reports/`. A separate `exports` package isn't worth it at this size.

**1. A new table, `report_exports`**
```sql
CREATE TABLE report_exports (
  id           INTEGER PRIMARY KEY,
  user_id      INTEGER NOT NULL,
  report_id    INTEGER NOT NULL,
  report_title TEXT    NOT NULL,   -- copy of the title at export time
  exported_at  TEXT    NOT NULL    -- ISO-8601 UTC
);
CREATE INDEX ix_report_exports_user_time ON report_exports(user_id, exported_at DESC);
```
- Save a copy of the title rather than joining to `reports` at read time. The history should show what the user actually exported, and the entry should survive the report being renamed or deleted.
- Key the table on the user who ran the export, not the report owner. They're the same person today, but they won't be once reports are shared.
- Someone needs to find out where `reports` and `users` get created, because that isn't in `fixture/`, and add this table in the same place.

**2. `app/reports/models.py`: two new functions in the existing style**
- `record_export(user_id, report_id, title)`: a single `INSERT` through `execute()`.
- `recent_exports(user_id, limit=10)`: `SELECT report_title, exported_at ... ORDER BY exported_at DESC LIMIT ?`.
- Don't delete old rows at launch. The `LIMIT` already handles "last few", and cleaning up old rows can come later.

**3. `app/reports/csv_export.py`: a new module with no database access**
- `report_to_csv(report) -> str`, using the standard `csv` module and `io.StringIO`.
- It has to list the column headers explicitly, because `execute()` returns plain tuples.
- **Spreadsheet formula injection:** a cell that starts with `=`, `+`, `-`, `@`, tab or carriage return is treated as a formula when the CSV is opened in Excel or Sheets. Titles and bodies are user-written, so prefix such cells with `'`.
- Since this module has no database access, it's easy to unit-test.

**4. `app/reports/views.py`**
- A new `report_export_csv(request, report_id)`: run the owner-scoped fetch (404 on a miss), build the CSV, call `record_export`, then return the file.
- Only log the export after the CSV has been built successfully, so failed attempts don't show up in the history.
- `report_list` also passes `recent_exports(request.user_id)` to the page so it can show the history.
- **The response is the main thing to design up front.** Today `render()` returns raw data, but a download needs `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="..."`. Clean the filename built from the title: remove quotes, newlines and path characters.
  - Whoever owns the real web framework needs to say how a view returns a response with custom headers.
  - The export must be a GET request with no side effects other than the log entry, and it must check login like the other report views.

## Questions for product before coding

1. **What goes in the CSV?** A report is a single `body` text field, so as it stands the CSV would have one row: `id, title, created_at, body`. If product expects the report's underlying data rows, that's a much bigger feature, and the data source isn't in this code.
2. **How many entries is "the last few"?** I've assumed 10.
3. **Do history entries need a link to re-download?** Copying the title supports showing entries, and storing `report_id` keeps re-download possible later.
4. **Timezone:** store times in UTC and convert to the user's local time on display. I'm assuming nothing records a user's timezone today, since `users` only has `id, email`.

## Suggested PR order

1. The ownership fix on `report_detail`. It's a security fix and should ship by itself.
2. The table, plus `record_export` and `recent_exports` with tests.
3. `csv_export.py` with tests, including the formula-injection and Unicode cases.
4. The export view and button, plus the history on the list page.