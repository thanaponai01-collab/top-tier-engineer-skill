I read all of `fixture/`. It's four small files, about 50 lines total. Here's how I'd structure this, followed by a few things to settle before anyone starts coding.

## What's there now

- **`app/db.py`** is the only place that talks to SQLite. `execute()` opens a connection, runs one query, commits, and returns `fetchall()`.
- **`app/reports/models.py`** has plain functions with raw SQL that return tuples: `list_reports(owner_id)` and `get_report(report_id)`. `app/users/models.py` follows the same pattern.
- **`app/reports/views.py`** has `report_list` and `report_detail`. `render()` is a stub that just returns the data. There's no response object, headers or content type anywhere.
- There's no schema or migrations directory in `fixture/`, so the tables are defined somewhere else.

## Proposed structure

Keep the current pattern (function-based models and SQL only through `db.execute`) and don't add any new layers.

**1. New table `report_exports`**
```sql
CREATE TABLE report_exports (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER NOT NULL,
  report_id   INTEGER NOT NULL,
  title       TEXT    NOT NULL,   -- snapshot at export time
  exported_at TEXT    NOT NULL    -- UTC ISO-8601
);
CREATE INDEX idx_report_exports_user_time ON report_exports (user_id, exported_at DESC);
```
Store a copy of the title rather than looking it up by joining to `reports`. That way the history still shows the right name if a report is later renamed or deleted, and reading the history is a single-table query.

**2. `app/reports/models.py`**: add two functions next to the existing ones:
- `record_export(user_id, report_id, title)`
- `list_recent_exports(user_id, limit=5)`, using `ORDER BY exported_at DESC LIMIT ?`

For launch, just read the latest N rows; no pruning job is needed.

**3. `app/reports/csv_export.py`** (new): a pure function that turns report data into CSV text using the stdlib `csv` module. It shouldn't touch the database or the request, so it's trivial to unit test. It also needs to guard against CSV/formula injection: any cell starting with `=`, `+`, `-`, `@`, tab or CR should get a `'` prefix, because these files will be opened in Excel.

**4. `app/reports/views.py`**:
- `report_export_csv(request, report_id)`: fetch the report, check that the user owns it, build the CSV, call `record_export`, then return the file. Record the export only after the CSV has been built, so failed attempts don't show up in the history.
- Add `list_recent_exports(request.user_id)` to what `report_list` renders, so the history appears on the reports page. A separate endpoint isn't needed.

## Things to settle first

1. **`report_detail` has no ownership check.** `get_report(report_id)` doesn't filter by owner, so any user can currently read any report by its ID. If the export reuses it as-is, anyone could also download any report as a CSV. I'd add a `get_report_for_owner(report_id, owner_id)` (or an owner check in the view) and use it for both detail and export. This should probably be fixed on its own, regardless of the CSV work.
2. **What exactly goes in the CSV?** "Download as CSV on the reports page" could mean either:
   - the list of reports (id, title, created_at), or
   - one report's contents.

   If it's one report's contents, `body` is a single opaque column and nothing in `fixture/` shows its structure, so we'd need to know what it contains before we can turn it into rows. Product needs to answer this before `csv_export.py` can be designed.
3. **There's no way to return a file yet.** `render()` returns raw data, so a download needs a response with `Content-Type: text/csv` and `Content-Disposition: attachment`. That depends on the framework in use, which I can't see from `fixture/`. Someone needs to decide whether `render` grows that ability or the export view builds its own response.
4. **Where does the schema live?** Since there are no migrations here, the new table has to be added wherever the `reports`/`users` tables are defined. The existing `created_at` format is also unknown, and `exported_at` should match it.

Once those four are answered, this is roughly one new table, two model functions, one small CSV module and one new view, plus tests for the CSV function and the ownership check.