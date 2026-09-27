I read all four files in `fixture/app/` (about 50 lines total). The design mostly follows existing patterns, but there's one security problem to fix first and a few product questions to answer before anyone writes code.

## What the code does today

- **`app/db.py`** is the only place that opens a SQLite connection. Every query goes through `execute()`, which opens a connection, commits, and closes it on each call.
- **`app/reports/models.py`** and **`app/users/models.py`** are plain functions that run raw SQL and return tuples. There's no ORM and no migrations folder, so it isn't clear where table definitions live.
- **`app/reports/views.py`** has two views. `render()` is a stub that returns its input, so there's no visible way to set headers or content types yet.

## Fix first: anyone can read any report

`report_detail` calls `get_report(report_id)` without checking who owns the report (`views.py:9-11`), and `get_report` doesn't even select `owner_id`. So any logged-in user can open any report by guessing its ID. A CSV export built on `get_report` would let them download it too.

**Fix:** add an owner-scoped lookup such as `get_report_for_owner(report_id, owner_id)` using `WHERE id = ? AND owner_id = ?`. Use it in both the existing detail view and the new export view. This should ship before or with the export button.

## Proposed structure

**1. CSV conversion: new file `app/reports/export.py`**
- One function, `report_to_csv(report) -> str`, using Python's built-in `csv` module. It has no database access, so it can be unit-tested on its own.
- Guard against spreadsheet formula injection: if a cell starts with `=`, `+`, `-`, `@`, tab or carriage return, put a `'` in front. Titles and bodies are user-entered, so a title like `=HYPERLINK(...)` would otherwise run when opened in Excel.

**2. Export history: a new table plus two functions in `app/reports/models.py`**

```sql
CREATE TABLE report_exports (
  id           INTEGER PRIMARY KEY,
  user_id      INTEGER NOT NULL,
  report_id    INTEGER,               -- nullable / no cascade: history survives report deletion
  report_title TEXT NOT NULL,         -- snapshot at export time
  exported_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
);
CREATE INDEX idx_report_exports_user_time ON report_exports (user_id, exported_at DESC);
```

- `record_export(user_id, report_id, title)` saves one row.
- `list_recent_exports(user_id, limit=5)` returns the newest rows first, using `ORDER BY exported_at DESC LIMIT ?`.
- Both go through `app.db.execute`, like the rest of the code.
- I'd save a copy of the title rather than join to `reports`. The history then shows what the user actually exported, even if the report is later renamed or deleted.

**3. Views: `app/reports/views.py`**
- Add `report_export_csv(request, report_id)`:
  1. Load the report with the owner-scoped lookup, returning 404 if it isn't found or isn't theirs.
  2. Build the CSV.
  3. Save the history row.
  4. Return the file.
- Save the history row only after the CSV builds successfully. `execute()` commits after every call, so this can't be one transaction. That's fine here, since the worst case is a missing history row.
- Add the recent exports to what `report_list` passes to the page, so the reports page can show them next to the button.

## Questions to answer before coding

1. **What goes in the CSV?** A report is just `id, title, created_at, body`. Is it one report's `body` turned into rows, or the whole report list as a table? The shape of `body` (free text or structured data) decides this, and it's the biggest unknown.
2. **Where do table definitions live?** There's no schema file or migrations here. Someone needs to say where the `CREATE TABLE` goes.
3. **How do responses work?** `render()` is a stub. A download needs `Content-Type: text/csv` and `Content-Disposition: attachment; filename="..."`, and nothing here shows how to set those.
4. **How many is "a few", and how long do we keep them?** I'd show the last 5. We don't need to delete old rows yet, but agree whether a cleanup job is needed later.
5. **Timestamp format:** I'd store UTC in ISO format. Check how the existing `reports.created_at` is stored so the two match.