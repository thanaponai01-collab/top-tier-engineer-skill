Everything belongs inside `app/reports/`. You need one new file for turning a report into CSV, one new view for the download, and later one small history table. The hard-to-reverse choice is how export history is stored, and I need your answer on that before anyone designs it. There's also something to fix first: **any logged-in user can read any report by guessing its id**, and a CSV export built the same way would leak reports too.

The plan is in `fixture/docs/arch-design-csv-export.md`.

## What I found
- **The layout is sound.** `app/db.py` is the only place that talks to the database, and each area writes its own queries. No restructuring is needed.
- **Reports aren't checked against their owner.** `get_report(report_id)` (`app/reports/models.py:10`) doesn't look at who is asking. I ran it with a throwaway database: user 8 got back user 7's report through `report_detail` (`app/reports/views.py:10`). A separate check agreed.
- **There's nowhere to declare a new table.** The repo has no table definitions or migrations; the `reports` and `users` tables are defined somewhere outside `fixture/`.
- **Nothing in `fixture/` can mark a response as a file download.** `render()` (`views.py:14`) just returns its input. The download view will have to use the real web framework's response, which isn't in this folder.

## The work, in order (these three can start now)
1. **Make every read by id check the owner.** Change it to `get_report(report_id, owner_id)` and pass `request.user_id` from `report_detail`. This also fixes the existing report page, but it changes behaviour: first confirm that no admin or shared-report screen relies on reading other users' reports.
2. **Add `app/reports/csv_export.py`** with a `report_to_csv(row)` function built on Python's standard `csv` module (no new dependency). Any cell starting with `=`, `+`, `-` or `@` gets a leading quote so Excel won't run it as a formula. I tested the check command for this step against a throwaway version, which I then deleted; it passes.
3. **Add a `report_export_csv` view** that uses the owner-checked read, returns "not found" for anyone else, and sends `text/csv` as a file download. The button links to it. Keep the export code in the reports area for now; only move it to a shared place when a second area needs exports.

## Needs your yes before it's planned: how history is stored
Adding a table can't be quietly undone once it holds data, so I left these steps out of the file until you choose:
- **A (recommended):** a `report_exports` table with `id, user_id, report_id, report_title, exported_at`. The title is copied at export time, so history still reads correctly after a report is renamed or deleted. The download view writes one row per export, and the history list shows the newest 5 for the current user. Old rows are kept; nothing is deleted at launch.
- **B:** store only `report_id` and look up the title when showing history. It's smaller, but renamed reports show their new title and deleted reports need special handling.
- **C:** keep history only in the browser (localStorage). No database change, but it's per device and disappears when the browser data is cleared.
- **If we pick wrong:** A→B is an easy later migration. Going from C to A means the history users already see is lost.

## Two product questions that change the work
1. **Is the button on a single report's page or on the list of reports?** I assumed one report, because the history shows a report title. If it's the list, the CSV has one row per report instead.
2. **What is in a report's `body`?** I assumed plain text going into one cell. If it's structured (like a table), the CSV should spread it into columns.

## What I didn't do
- There's no git history in `fixture/`, so there was no record of past changes to learn from; the plan rests only on reading the code.
- The file's automated check found **0 problems**. Its one warning is only that there's no commit to date the plan against.
- I didn't draw a diagram; three small steps didn't need one.
- The download step's final check (clicking the button in the running app) needs the web framework that lives outside `fixture/`.

<!-- file written by the agent: fixture/docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; analysis true of the working tree on 2026-09-27)
- question: where do "download report as CSV" and a per-user "recent exports" history live in fixture/, and what must be true before they're built?
- yardstick: add CSV download of a report (2 modules: app/reports, plus a new table if history is stored); add recent-exports history (1 module: app/reports, plus schema); add a second export format or a history field such as row count (1 module: app/reports, if Decision 1 holds)
- status: open
- verdict: clean. db.py is the only place that opens connections, and each domain module owns its own SQL. The one blocking problem is Finding 1: reads by report id are not scoped to the owner.
- context: export is per report (the history shows a report title); the CSV at launch is one header row + one data row: id,title,created_at,body; app/db.py stays the only connection owner; no new dependencies. Moves for storing and showing history are held until the user answers the storage question in chat (a one-way door).

## Finding 1: Reading a report by id doesn't check who owns it, so an export built the same way would leak other users' reports
- where: app/reports/models.py:10, app/reports/views.py:10
- cost: 1 of 2 read paths is unscoped. Reproduced: user_id=8 got report 1 (owner_id=7) back from report_detail
- badge: strong
- evidence: proven. Ran report_detail against a temp sqlite db as a non-owner and got the row back. A subagent that was not told the expected answer independently confirmed get_report(report_id) takes no user value (views.py:10)

## Finding 2: The repo has no schema or migration home, so the history table has nowhere to be declared
- where: app/db.py:4
- cost: 0 CREATE TABLE statements in the repo; 2 tables used (reports, users) are defined outside it
- badge: strong
- evidence: traced. grep for CREATE found nothing; the subagent also found no migrations

## Finding 3: There is no HTTP response type, so a view can't set Content-Type or Content-Disposition
- where: app/reports/views.py:14
- cost: render() returns its argument unchanged; a CSV download needs text/csv plus an attachment filename
- badge: worth exploring
- evidence: traced. fixture/ has no framework or routes, so the real response object lives outside it

## Decision 1: Where CSV serialization lives
- options: app/reports/csv_export.py (reports owns its own export) | a generic app/exports/ package for all domains
- forces: there is 1 exporter today; a generic package would have one caller (bar: inline it). Formats change for report reasons, which passes the same-reason test for keeping it inside reports
- door: two-way. Move it to a shared package when a second domain needs export
- evidence: traced. Read all 4 files; only reports has anything to export

## Decision 2: CSV library
- options: stdlib csv | pandas or another dependency
- forces: we write 4 columns and 1 row; a dependency would be <10% used
- door: two-way
- evidence: traced. Python 3.11.15 stdlib csv, no dependency manifest in fixture/

## Move 1: Scope get_report by owner so every read by id is owner-checked
- cost: any user can read any report by id (Finding 1), and the export would inherit this
- pays: the CSV export route is safe on day one instead of repeating the leak; add CSV download: 0 extra auth code
- files: app/reports/models.py:10, app/reports/views.py:10
- owner: app/reports/models.py get_report(report_id, owner_id), with SQL `WHERE id = ? AND owner_id = ?`
- callers: app/reports/views.py:10 (report_detail: pass request.user_id). The Move 3 view is the only other caller
- door: two-way code change, but it changes behavior: non-owners now get None from report_detail. Confirm that no admin or shared-report path depends on the old behavior before landing
- proof: from fixture/: python3 -c "import app.db as d,tempfile;d.DB_PATH=tempfile.mktemp();d.execute('CREATE TABLE reports(id INTEGER PRIMARY KEY, owner_id INT, title TEXT, created_at TEXT, body TEXT)');d.execute(\"INSERT INTO reports VALUES(1,7,'Q3','2026-09-01','x')\");from app.reports.models import get_report as g;assert g(1,7) and g(1,8) is None;print('OK')" prints OK
- effort: S
- after: nothing

## Move 2: Add a pure CSV serializer in the reports module
- cost: nothing serializes a report today
- pays: add CSV download: the format lives in 1 file; adding a format later adds 1 sibling file and touches nothing else
- files: app/reports/models.py:12
- owner: new app/reports/csv_export.py: report_to_csv(row) -> str, using csv.writer on io.StringIO with header id,title,created_at,body taken from the SELECT column order at models.py:12. Put a single quote in front of any cell that starts with = + - @ \t \r, so spreadsheets don't run it as a formula (CSV injection)
- callers: the Move 3 view only
- door: two-way
- proof: from fixture/: python3 -c "from app.reports.csv_export import report_to_csv as f;o=f((1,'=HYPERLINK(1)','2026-09-01','a,b\nc'));print(o);assert o.splitlines()[0]=='id,title,created_at,body' and \"'=HYPERLINK\" in o and '\"a,b' in o;print('OK')" prints OK
- effort: S
- after: nothing

## Move 3: Add the owner-scoped CSV download view
- cost: no download entry point exists
- pays: add CSV download: 1 view plus 1 route in the host app; history later hooks into this one function
- files: app/reports/views.py:9
- owner: app/reports/views.py report_export_csv(request, report_id): calls get_report(report_id, request.user_id), returns not-found if None, otherwise returns report_to_csv(...) with Content-Type text/csv; charset=utf-8 and Content-Disposition attachment; filename="report-<id>.csv". The response object comes from the host framework (Finding 3). Wire the button on the report page to this route
- callers: the new route in the host app; the "Download as CSV" button
- door: two-way
- proof: from fixture/, with the temp-db setup from Move 1: calling report_export_csv as owner 7 returns a body whose first line is id,title,created_at,body; as user 8 it returns not-found and no body. Then in the running app, click the button and the browser saves report-1.csv
- effort: S
- after: Move 1, Move 2
