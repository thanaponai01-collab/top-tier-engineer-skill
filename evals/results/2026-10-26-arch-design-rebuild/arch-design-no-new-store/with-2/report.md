The code is in good shape for this feature, but fix one security hole before building it. Opening a report by its id never checks who owns it, so a CSV export built on that same lookup would let any user download any report.

## What I found

**1. Opening a report doesn't check the owner (I confirmed this by running it).**
`get_report` (`app/reports/models.py:10`) looks a report up by id alone, and `report_detail` (`app/reports/views.py:9`) uses it. In a temporary copy of the code, user 99 asked for report 1 and got user 7's full report text back. If the export button reuses that lookup, anyone can download anyone's report as CSV by guessing ids.

**2. Nothing is saved per user yet, so export history needs one new table.**
The code only reads two tables, `reports` and `users`. The repo has no file that creates tables (no schema or migrations), so whoever adds the history table also has to decide where its create statement lives. The cost is one new table, two new database functions and two new pages. No existing function changes.

## Recommended structure

Put both features in the reports module and route every export through an owner-checked lookup:

1. **Add `get_report_for_owner(report_id, owner_id)`** in `app/reports/models.py`, which filters on `id = ? AND owner_id = ?`. Switch `report_detail` to it. Keep `get_report` for now so nothing else breaks.
2. **Add a `report_exports` table** with columns `id, owner_id, report_id, report_title, exported_at`. Add `record_export(owner_id, report)` and `list_exports(owner_id, limit=5)` in `app/reports/models.py`. Both run their queries through `app.db.execute` (`app/db.py:11`), which already handles every query and connection.
3. **Add `report_export_csv(request, report_id)`** in `app/reports/views.py`. It looks the report up with the owner-checked function and returns 404 if that finds nothing. It builds the CSV with Python's built-in `csv` module and records the export only after the CSV is built.
4. **Add `export_history(request)`**, which returns `list_exports(request.user_id)`.

Only one file uses the code that changes: `app/reports/views.py:1`.

### The decision that's hard to undo: where history lives
Saving history means storing data, so it's worth deciding on purpose. I ranked what matters first:
1. Users can only export, or see history for, their own reports.
2. History follows the user across devices, and still reads correctly after a report is renamed or deleted.
3. The change stays small and matches how the code already queries the database.

- **Option A (recommended):** a server-side `report_exports` table that saves the report's title as it was at export time.
- **Option B:** no server storage; the browser keeps the list locally after each download.

I chose A because of point 2. Browser-only history disappears on another device and can't be audited. Adding the table later would also wipe whatever history users saw at launch. Saving the title, rather than only looking it up from the report, keeps old entries readable after a rename or delete.

### Check to rerun after each step
This currently passes on a copy of the code. Run it from `fixture/` after every step to confirm the existing report list and lookup still behave the same:
```
python -B -c "import os,tempfile,app.db as d; d.DB_PATH=os.path.join(tempfile.mkdtemp(),'t.db'); d.execute('CREATE TABLE reports(id INTEGER PRIMARY KEY, owner_id INT, title TEXT, created_at TEXT, body TEXT)'); d.execute(\"INSERT INTO reports VALUES(1,7,'Q3','2026-10-01','x')\"); from app.reports import models as m, views as v; R=type('R',(),{'user_id':7}); assert v.report_list(R())==[(1,'Q3','2026-10-01')]; assert m.get_report(1)[1]=='Q3' and m.get_report(2) is None; print('ok')"
```
When the export is built, also add a check that a different user asking to export report 1 gets a 404.

## Also noticed while reading
- **Security:** the ownership hole in finding 1 already affects the existing report detail page, not just the new export.
- `DB_PATH = "app.sqlite3"` in `app/db.py:4` is a relative path, so which database file the app opens depends on the folder it's started from.
- `render()` in `app/reports/views.py:14` just returns its input unchanged. The CSV view will need to return a real file download with the right headers, which the codebase has no example of yet.

I didn't change anything in `fixture/`. All testing ran in a temporary copy that has since been deleted. There's only one move worth making here; if you agree with Option A, I can implement it, starting with the ownership fix.