The codebase is small: four files, 53 lines. That makes the structure easy to pick, but it also shows a few gaps to deal with first.

## What's there now

- **`app/db.py`** is the only way anything talks to the database. `execute()` opens a connection, runs one parameterized query, commits, and closes.
- **`app/<domain>/models.py`** files are plain functions wrapping SQL, like `list_reports` and `get_report`. They return raw row tuples.
- **`app/reports/views.py`** has views that call the model functions and pass the result to `render()`, which currently just returns the data unchanged.
- There's no schema file, migrations, or tests in `fixture/`. The `users` and `reports` tables are only implied by the queries.

## Proposed structure

Keep everything inside `app/reports/` and follow the existing pattern. A new top-level `exports` domain isn't worth it for one table.

**1. New table `report_exports`**

```
id, user_id, report_id, report_title, exported_at (UTC ISO-8601)
index on (user_id, exported_at)
```

- Save `report_title` as it was at export time rather than joining to `reports`. The history should show what the user actually downloaded, even if the report is later renamed or deleted.
- There's nowhere to put this DDL yet (see open questions).

**2. `app/reports/models.py`: two new functions, same style as the current ones**

- `record_export(user_id, report_id, title)`
- `list_recent_exports(user_id, limit=5)`, which does `ORDER BY exported_at DESC LIMIT ?`

Both should go through `execute()`. Showing only the last few can be done with the `LIMIT` when reading. Pruning old rows can wait until after launch.

**3. `app/reports/csv_export.py`: a pure function `report_to_csv(report) -> str`**

- It uses the `csv` module and has no database or request code, so it's easy to unit test.
- It should escape cells that start with `=`, `+`, `-` or `@`. Report titles and bodies are user-entered, and without that escaping a crafted value runs as a formula when someone opens the file in Excel.

**4. `app/reports/views.py`**

- Add a `report_export_csv(request, report_id)` view. It fetches the report, checks ownership, builds the CSV, records the export, and returns a response with `Content-Type: text/csv` and a `Content-Disposition: attachment; filename=...` header.
- Have `report_list` also call `list_recent_exports(request.user_id)` so the history appears on the reports page.

## Fix before building this

1. **Anyone can open any report.** `report_detail` → `get_report(report_id)` never checks `owner_id`, so any user can view any report by changing the ID. A CSV export built the same way would let people bulk-download other users' data. Add an ownership-checked lookup, e.g. `get_report_for_owner(report_id, owner_id)` or a check in the view, and use it for both the existing detail view and the new export view.
2. **`render()` can't send a file.** It's a stub that returns data, with no way to set a content type or headers. Someone needs to confirm what framework or response object sits behind it. Otherwise the CSV view will have to work around it in an ad hoc way.

## Questions for product and engineering

- **What goes in the CSV?** A report row has only `id, title, created_at, body`. Is the CSV just that one row, or is `body` structured data that should become rows and columns? This matters most, because it decides what `report_to_csv` actually does.
- **Should one download link export several reports**, or is it one report per click? The history design works either way, but the view and filename don't.
- **What counts as "an export"?** We can record the moment we generate the file, but not whether the download finished. That's probably fine for launch; it just needs to be agreed.
- **Where do schema changes go?** With no migrations in `fixture/`, someone needs to decide where the `CREATE TABLE` belongs.
- **How long to keep history?** "Last few" is covered by the `LIMIT`. If there's any compliance or storage limit on audit-like records, a pruning job is needed. If not, it can be skipped for now.

Suggested order: fix the ownership check first, then the CSV function with tests, then the table and model functions, then the view and the history on the list page.