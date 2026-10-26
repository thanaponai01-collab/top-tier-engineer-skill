I read all four files in `fixture/`: `db.py`, `reports/models.py`, `reports/views.py` and `users/models.py`. Two things need deciding before anyone writes code: what goes in the CSV, and the ownership check described below.

## What's there now

- **`app/db.py`** is the only place that talks to the database. `execute()` opens a connection, runs one query, commits and closes.
- **`app/reports/models.py`** has plain query functions (`list_reports`, `get_report`). There are no ORM classes.
- **`app/reports/views.py`** has thin view functions. `render()` is a stub that returns the data unchanged.
- There's no schema or migrations file, no routing and no response object anywhere in the fixture.

## Proposed structure

Follow the existing layout and add nothing new at the top level.

**1. New table `report_exports`**
```sql
CREATE TABLE report_exports (
  id           INTEGER PRIMARY KEY,
  user_id      INTEGER NOT NULL,
  report_id    INTEGER NOT NULL,
  report_title TEXT    NOT NULL,   -- copy of the title at export time
  created_at   TEXT    NOT NULL    -- UTC, set by the server
);
CREATE INDEX report_exports_user_created ON report_exports(user_id, created_at DESC);
```
Store a copy of the title rather than joining to `reports`. Otherwise a report that's renamed or deleted later would change or break the user's history.

**2. `app/reports/models.py`: two more query functions, in the same style as the existing ones**
- `record_export(user_id, report_id, title)`
- `list_recent_exports(user_id, limit=5)`, sorted newest first with `LIMIT ?`.

Keep every row and limit only when reading. Add pruning later if the table gets large.

**3. `app/reports/csv_export.py` (new): one pure function, `report_to_csv(report) -> str`**
- It uses Python's `csv` module and doesn't touch the database or the request, so it's easy to unit test.
- It must escape cells that start with `=`, `+`, `-` or `@`. Report titles and bodies are user-written, and a spreadsheet would run those cells as formulas.

**4. `app/reports/views.py`: two new views**
- `report_export_csv(request, report_id)`: load the report, check ownership, build the CSV, then call `record_export`. Record the export only after the CSV builds successfully, so failed exports don't show up in the history.
- `report_export_history(request)`: returns `list_recent_exports(request.user_id)`.

## Things to fix or decide first

1. **There's no ownership check.** `get_report(report_id)` (`app/reports/models.py:10`) doesn't filter by owner, and `report_detail` doesn't check either. Any user can already read any report by its ID. A CSV download would make that worse by letting people bulk-download other users' reports. Fix it before building on it: either `get_report(report_id, owner_id)` with `AND owner_id = ?`, or a check in the view.
2. **What goes in the CSV isn't defined.** A report is just `id, title, created_at, body`, with `body` as one text field. A CSV of a single row isn't much use. Product needs to say whether `body` holds table-shaped data and, if so, in what format. That answer determines `report_to_csv`, which is the only part of the plan it affects.
3. **There's no response object.** `render()` returns raw data, but a download needs `Content-Type: text/csv` and a `Content-Disposition` header with a safe filename built from the title. Find out what the real framework provides, or extend `render`.
4. **Where does the schema change go?** There's no migrations folder in the fixture, so confirm where `CREATE TABLE` statements live in the real app.
5. **How many is "last few"?** I'd use 5 for launch. Saving the full history now and limiting when reading means this can change later without a migration.

## Suggested order

1. Ownership fix, with a test.
2. Table, plus `record_export` and `list_recent_exports`.
3. `report_to_csv`, once the content question is answered.
4. The two views and the button.

Steps 2 and 3 can be built at the same time.