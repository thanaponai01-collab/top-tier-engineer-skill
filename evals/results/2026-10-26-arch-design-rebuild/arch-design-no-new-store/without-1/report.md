I've read all of `fixture/`. It's four small files: `app/db.py`, `app/reports/models.py`, `app/reports/views.py` and `app/users/models.py`. My recommendation follows, and there are three things to settle first.

## Settle these first

1. **A missing ownership check.** `report_detail` (`app/reports/views.py:9`) calls `get_report(report_id)`, and that query (`app/reports/models.py:10`) doesn't filter by owner. So any user can fetch any report by its ID. An export endpoint copied from `report_detail` would let anyone download anyone's report as a file. Fix it before or alongside the export work: change it to `get_report(report_id, owner_id)` with `WHERE id = ? AND owner_id = ?`, and have both views use it.
2. **It's unclear what goes in the CSV.** A report is only `id, title, created_at, body`, and `body` is one blob. Product needs to say which they mean:
   - (a) the reports *list* page exported as rows of title and date, or
   - (b) one report's contents. If it's this one, what format is `body` in, and how does it become rows and columns?

   This decides whether the endpoint is `report_list_export(request)` or `report_export(request, report_id)`. The history design below works for either.
3. **The framework isn't in the fixture.** `render()` just returns the data unchanged. There's no response object, no routing and no schema or migrations folder, so there's no visible way to set a CSV content type or a download filename. We need to know what really serves these views and where table definitions live.

## Recommended structure

**Data: a new table `report_exports`**
```
id           INTEGER PK
user_id      INTEGER NOT NULL
report_id    INTEGER NULL      -- NULL if it's a list export
title        TEXT NOT NULL     -- title as it was at export time
exported_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
INDEX (user_id, exported_at DESC)
```
Save the title at export time instead of joining to `reports` later. That way the history stays correct if a report is renamed or deleted, and reading the history needs no join.

**Model: add to `app/reports/models.py`**
- `record_export(user_id, report_id, title)`
- `list_recent_exports(user_id, limit=5)`, which runs `ORDER BY exported_at DESC LIMIT ?`

All SQL should keep going through `db.execute`, since that's the one place the codebase talks to the database. The history belongs to reports, so it doesn't need its own `exports` package yet.

**CSV conversion: a new file, `app/reports/csv_export.py`**
- One function, `to_csv(rows, columns) -> str`, built on the `csv` module from Python's standard library. It touches no database and no request, so it's easy to unit-test.
- It should neutralise "CSV injection": a cell starting with `=`, `+`, `-` or `@` can run as a formula when opened in Excel, so prefix those with `'`. Report titles and bodies are typed by users, so this matters.

**Views: add to `app/reports/views.py`**
- `report_export(request, ...)` should:
  1. load the data with the owner-scoped query,
  2. return 404 if it isn't found,
  3. call `to_csv`,
  4. call `record_export`,
  5. return the response as a file download (CSV content type, with a filename).

  Record the export only after the CSV is built, so a failed export doesn't show up in the history.
- To show the history, either add `list_recent_exports(request.user_id)` to what `report_list` returns, or add a small `export_history` view. Adding it to `report_list` is simpler if the history appears on the reports page itself.

## Decisions to make now
- **How many to keep:** show the last 5 with `LIMIT`, and don't delete old rows at launch. The table stays small, and you keep the option of a longer history later.
- **Big reports:** build the CSV in memory for launch, given how small reports currently look. Switch to streaming if reports get large.
- **Two separate database calls:** `db.execute` opens a fresh connection each time, so writing the history row and reading the report aren't one transaction. That's acceptable here because a missing history row is harmless. Just don't build anything that assumes they happen together.

## Suggested order
1. Owner-scope `get_report` and fix `report_detail`.
2. Create the `report_exports` table.
3. Write `csv_export.py` with its tests.
4. Add the model functions and the export view.
5. Add the history to the reports page.