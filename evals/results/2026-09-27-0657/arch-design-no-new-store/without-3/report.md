I read everything in `fixture/`: four files, 53 lines. There's a single DB helper (`app/db.py`), models that hold raw SQL, views that call models, and `render()` is a stub. There's no schema, no migrations, no tests and no HTTP framework, so I've kept the plan to those same layers.

## Proposed structure

**1. CSV generation: new `app/reports/export.py`**
- One function, `report_to_csv(report) -> str`, built on the standard `csv` module. It takes a row and returns text, with no DB or request access, so it's easy to unit-test.
- Guard against formula injection: if a cell starts with `=`, `+`, `-` or `@`, prefix it with `'`. Report titles and bodies are user-supplied, and these files will be opened in Excel.

**2. Export history: add to `app/reports/models.py`**
- New table `report_exports(id, user_id, report_id, title, exported_at)`.
- Save a copy of the **title at export time**, not just `report_id`. History should show what the user actually downloaded, even if the report is later renamed or deleted, and it avoids a join.
- Store `exported_at` as UTC ISO-8601 and convert for display in the UI.
- Two functions, following the same pattern as the existing code:
  - `record_export(user_id, report)`: an `INSERT` through `execute`.
  - `recent_exports(user_id, limit=5)`: `... WHERE user_id = ? ORDER BY exported_at DESC LIMIT ?`.
- Show only the last few via `LIMIT`; don't delete older rows for launch. Cleanup can come later if the table grows.

**3. Views: `app/reports/views.py`**
- `report_export(request, report_id)`: fetch the report, check ownership, build the CSV, call `record_export`, and return the file.
  - Record the export only after the CSV is built, so failed exports don't show up in history.
- Show the history on the existing `report_list` page by calling `recent_exports(request.user_id)`, rather than adding another endpoint.

## Things to settle before coding

1. **Security bug: `report_detail` has no ownership check.** `get_report(report_id)` fetches any report by ID (`views.py:9-11`), so any user can read any report. If the export copies this pattern, anyone could download anyone's reports as CSV. Fix it first: either `get_report(report_id, owner_id)` with `AND owner_id = ?`, or a check in the view. It's a small fix but should be its own change.
2. **What goes in the CSV? (for Product)** A report has `id, title, created_at, body`. If `body` is free text, a one-row CSV isn't very useful. Is the button meant for:
   - a single report's contents? That needs `body` to be tabular, or a known format we can parse.
   - the list page, exporting every report the user owns? This fits "on the reports page" better, but then "report title" in the history doesn't quite fit.

   This decides what `report_to_csv` takes as input, so it's the main open question.
3. **Schema management.** Nothing here creates tables; even `reports` and `users` aren't defined anywhere visible. Where do schema changes go?
4. **Response handling.** `render()` returns data unchanged, so there's currently no way to set `Content-Type: text/csv` or `Content-Disposition: attachment; filename=...`. We need to know what framework actually serves these views, or add a small response helper.
5. **Size.** Building the whole CSV in memory is fine if reports are small. If a single export can be large, we should stream it instead. Worth confirming typical sizes.

## Suggested order

1. Ownership fix, on its own.
2. `export.py` with unit tests (the first tests in the repo).
3. Table plus `record_export` / `recent_exports`.
4. Export view, and history on the list page.

Question 2 needs an answer before step 2 starts. Questions 3 and 4 need answers before steps 3 and 4.