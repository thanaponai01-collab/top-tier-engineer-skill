I ran arch-design in design mode over `fixture/`. All three stages passed (`ARCH-GATE: done`) and nothing in the repo changed. The probe ran in a throwaway copy and left no `__pycache__` or sqlite file behind.

**Verdict: the structure is clean, but one security hole needs fixing first.** The app is small, every query goes through one helper (`app/db.py::execute`) and one sqlite file, and the export feature fits into the existing reports module. The hole would carry straight into the export if we build on it as it is.

## Fix first: any user can read any report
`get_report(report_id)` (`app/reports/models.py:10`) doesn't check who owns the report, and `report_detail` (`app/reports/views.py:9`) calls it as is. I confirmed this in a temp copy: user 99 got back user 7's full report, body included. The CSV export will call the same function, so as written anyone who guesses an id could download someone else's report.

**Fix:** add an owner check, `get_report(report_id, owner_id)` with `AND owner_id = ?`, and pass `request.user_id` from the view. That's about 2 lines today; once the export exists there are two places that need it.

## Recommended structure
**Keep the export in the reports module and store the history as one new table in the existing sqlite database.**

1. Add the owner check to `get_report` (above).
2. Add a new table:
   `report_exports(id, user_id, report_id, title, exported_at)`, indexed on `(user_id, exported_at)`.
   The title is copied when the export runs, so the history still reads correctly after a report is renamed or deleted.
3. Add `record_export(user_id, report_id, title)` and `list_exports(user_id, limit=5)` to `app/reports/models.py`, both using `app.db.execute`.
4. Add `report_export_csv(request, report_id)` to `app/reports/views.py`:
   - load the report with the owner check;
   - write it out with Python's built-in `csv` module;
   - call `record_export`;
   - return it as a `text/csv` download (`Content-Disposition: attachment`).
5. Show the history with a small `recent_exports` view, or by adding `list_exports` output to `report_list`.

- **Only one file uses the code being changed:** `app/reports/views.py:1`.
- **Check:** this command passes today against a temp database. Rerun it after each step to confirm list and detail still behave the same for owners:
  ```
  python -B -c "import tempfile,os,app.db as d; d.DB_PATH=os.path.join(tempfile.mkdtemp(),'t.sqlite3'); d.execute('CREATE TABLE reports(id INTEGER PRIMARY KEY, owner_id INT, title TEXT, created_at TEXT, body TEXT)'); d.execute(\"INSERT INTO reports VALUES(1,7,'Q3','2026-10-01','x')\"); from app.reports import views; R=type('R',(),{'user_id':7}); assert views.report_list(R())==[(1,'Q3','2026-10-01')]; assert views.report_detail(R(),1)[1]=='Q3'; print('ok')"
  ```
- **Reuses:** `app/db.py:11`, which is already how both model modules talk to the database.

## Where to keep the history (a stored-data decision, hard to undo)
What matters, most important first:
1. History is per user and survives across devices and sessions.
2. No second data store to secure and back up.
3. It's the smallest base that a later "re-download" or audit feature can grow from.

- **A (chosen):** a table in the existing sqlite database.
- **B:** keep the last few exports in the browser's localStorage.

A wins on 1, because B loses the history on another browser or when storage is cleared. It also wins on 2, because it reuses the one database connection path.

**Not doing:** a separate history store (a file, Redis, or localStorage), or generating CSV files ahead of time on disk or through a job queue.
**If that call is wrong:** moving the history later means copying out one table. Choosing a separate store wrongly would mean a migration to merge it back, plus a second store to secure. Pre-generated CSV files would need cleanup and would put a second copy of report data on disk that also has to be protected.

## Other things I noticed
- **Security hole:** the missing owner check above. I proved it, and it should land before or together with the export.
- **Relative database path:** `DB_PATH = "app.sqlite3"` (`app/db.py:4`) depends on where the app is started from. Run it from a different directory and it silently creates a new, empty database. Worth making it a fixed absolute path before export history starts depending on it.
- **No schema files:** the repo has no table definitions or migrations, so we need to decide where the `CREATE TABLE report_exports` statement lives.

Should we go with this layout (owner check first, then the table plus the two views), or do you want to look at the localStorage option further?