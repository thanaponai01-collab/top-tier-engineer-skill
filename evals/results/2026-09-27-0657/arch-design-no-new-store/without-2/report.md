I read all four files in `fixture/`. It's a thin layer: `db.execute()` is the only way queries get run, model modules are plain functions that call it, and views call the models and then a stub `render()`. The design below follows that pattern. One existing bug needs fixing first, and a few questions need answers before anyone writes code.

## Fix first: anyone can read any report

`report_detail` (`app/reports/views.py:9`) calls `get_report(report_id)`, and that query (`app/reports/models.py:10`) doesn't filter by owner. Any user who guesses an id can read any report. A CSV export built on `get_report` would let them download it too, and would write another user's report title into their history.

**Recommendation:** change `get_report` to take an `owner_id` (`WHERE id = ? AND owner_id = ?`), or add a separate `get_report_for_owner`. Use it in both the detail view and the export. It's a small change, but it should ship before or alongside this feature.

## Proposed structure

**1. Data: add a `report_exports` table**
```sql
CREATE TABLE report_exports (
    id           INTEGER PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    report_id    INTEGER REFERENCES reports(id),
    report_title TEXT NOT NULL,          -- title as it was when exported
    exported_at  TEXT NOT NULL           -- ISO-8601 UTC
);
CREATE INDEX ix_report_exports_user_time ON report_exports (user_id, exported_at DESC);
```
- **Store the title at export time instead of joining to `reports`.** The history then still reads correctly if the report is renamed or deleted, and listing the history is a single query with no join. Keep `report_id` so the UI can link back to the report.
- `fixture/` has no schema or migrations, so someone has to decide where this DDL lives: whatever creates `users` and `reports` today, which isn't in the fixture.

**2. Model: new `app/reports/exports.py`**, in the same style as `models.py`:
- `record_export(user_id, report_id, title)`: one `INSERT` through `execute`.
- `recent_exports(user_id, limit=5)`: `SELECT report_id, report_title, exported_at ... WHERE user_id = ? ORDER BY exported_at DESC LIMIT ?`.

**3. CSV generation: a pure function, e.g. `app/reports/csv_export.py`**
- `report_to_csv(report) -> str`, built with `csv.writer` over an `io.StringIO`. It does no database work and knows nothing about requests, so it's simple to unit-test.
- **Guard against formula injection.** If a cell starts with `=`, `+`, `-`, `@`, a tab or a carriage return, prefix it with `'`. Otherwise a report whose title or body starts with `=HYPERLINK(...)` becomes a live formula when someone opens the file in Excel.

**4. View: add `report_export_csv(request, report_id)` in `views.py`**
1. Fetch the report with the owner-scoped query. If it's missing or belongs to someone else, return 404.
2. Build the CSV.
3. Call `record_export(...)`. Do this only after step 2 succeeds, so failed exports don't show up in history.
4. Return the CSV with `Content-Type: text/csv; charset=utf-8` and `Content-Disposition: attachment; filename="<safe-title>.csv"`.

`render()` is currently a stub that returns its data unchanged, with no way to set headers or a content type. The export needs a real response type, so check what the actual framework provides before building this view.

**5. History display:** `report_list` also calls `recent_exports(request.user_id)` and passes the result to the page, so no new endpoint is needed at launch. Add a JSON endpoint later if the frontend wants to refresh the list without reloading.

## Questions for product

- **What goes in the CSV?** A report only has `id, title, created_at, body`. If `body` is free text, the CSV is one row, which isn't very useful. If `body` holds tabular data (JSON, say), we need its format to pick the columns. This is the biggest unknown.
- **How many is "last few"?** I'd suggest 5–10. Should older rows be pruned, or kept for auditing and just hidden? Keeping them is cheap given the index.
- **Deleted reports in history:** show them greyed out without a link, or hide them? Storing the title snapshot supports either.
- **Time zone:** store UTC and convert to local time in the UI. Check what format `reports.created_at` uses so the two are consistent.

## Smaller notes

- Every `execute` call opens its own connection and commits (`app/db.py:11`). The export only writes one row, so that's fine here. If exports ever need to write more than one row atomically, `db.py` will need a transaction helper.
- There are no tests in `fixture/`. At minimum, add tests for `report_to_csv` (escaping, the injection guard, Unicode), for another user's report returning 404, and for `recent_exports` returning rows in order and respecting the limit.