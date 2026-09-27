I've written the design to `fixture/docs/arch-design-csv-export.md`. Both features fit inside `app/reports`, with no new module and no new dependency. Before anyone writes the export, one existing gap has to be fixed, and one storage decision needs your yes.

**Suggested structure**
- **CSV download:** add a new view `report_export_csv` in `app/reports/views.py`, with a small private `_report_to_csv()` helper that uses Python's standard `csv` module. It has only one caller today, so it doesn't need its own module. Move it out if XLSX or a second caller shows up.
- **Export history:** put `record_export()` and `list_recent_exports(user_id, limit)` in `app/reports/models.py`, and show the list on the reports page. History changes whenever export changes, so it belongs with reports. `app/users` doesn't need to know about exports.
- **Likely next changes:** a second format, or another field in the history, would each touch only the `reports` module.

**What to fix first**
`get_report` (`app/reports/models.py:10`) doesn't check who owns the report. `list_reports` filters by owner, `get_report` doesn't, and its one caller (`views.py:10`) passes only the report id. I read the whole chain, and a subagent recounted it independently and got the same numbers. If the CSV endpoint reused it as it is, any user could download any report by guessing ids. Move 1 in the file adds an owner check; Move 2 is the CSV view, including protection against spreadsheet formula injection (a title like `=HYPERLINK(...)`).

**Needs your yes (storage change, hard to undo)**
Export history needs somewhere to live, and there's no schema or migration file anywhere in `fixture/`, so the tables are created outside this tree. My recommendation is a new append-only table `report_exports(id, user_id, report_id, report_title, exported_at)`. It stores a copy of the title so the history still reads correctly after a report is renamed or deleted, and the page shows the newest 10.
- **Alternative:** keep the history in the browser (localStorage). It needs no schema change, but it wouldn't carry across devices or browsers.
- **Cost of choosing wrong:** a migration plus a backfill. Also, dropping the title copy later would lose the original names.

I left this out of the file as a move until you confirm it. Once you do, it becomes Move 3.

**Two questions for product**
1. What goes in the CSV? The report has a `body` column in an unknown format. Move 2 assumes the columns are `id, title, created_at, body`.
2. Does the history need to follow the user across devices? That decides between the table and localStorage.

**The file's check doesn't pass yet.** The checker found no missing fields, but it exits 1 on two things. `fixture/` isn't a git repository, so there's no commit to pin the design to. And without git it looks up file paths relative to `docs/`, so all 7 references like `app/reports/models.py:10` fail, even though they're correct from the repo root. Running `git init` and committing would fix both; I didn't do it because it changes your directory, so let me know if you want it.

I skipped a diagram, because it's two small changes in one module.

<!-- file written by the agent: fixture/docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; analysis is of the working tree on 2026-09-27)
- question: where do "download report as CSV" and a per-user export history (timestamp + report title) belong in fixture/app?
- yardstick: download one report as CSV (touches 1 module: reports, plus the schema-owner outside the repo = 0 today); show a user their last few exports (1 module: reports, plus a new table); add a field to history or a second format such as XLSX (1 module: reports)
- status: open
- verdict: clean — both features fit inside app/reports with no new module; one ownership gap must close first
- context: app/db.py stays the only place that opens connections; no new module, no new dependency (Python stdlib csv); the export-history table shape is parked until confirmed (see chat)

## Finding 1: get_report is not scoped to the requesting user, and the CSV export would become its 2nd caller
- where: app/reports/models.py:10, app/reports/views.py:9
- cost: 1 of 2 report queries filters by owner_id (list_reports does at models.py:6, get_report does not at models.py:12); 1 caller today (report_detail, views.py:10) passes a bare report_id; a download endpoint that reuses it lets any user export any report by guessing an id
- badge: strong
- evidence: traced, read every query and caller in fixture/app; no auth or routing layer exists in the fixture that could be checking ownership elsewhere

## Finding 2: no schema owner in the repo
- where: app/db.py:4
- cost: 0 CREATE TABLE or migration files in fixture/; users and reports tables are created somewhere outside the tree, so the new export-history table has no obvious home
- badge: worth exploring
- evidence: traced, listed all 4 files under fixture/

## Finding 3: views have no HTTP response shape
- where: app/reports/views.py:14
- cost: render() returns its input unchanged; a CSV download needs Content-Type text/csv and Content-Disposition attachment, and the fixture has no response object to set them on
- badge: worth exploring
- evidence: suspected, the real framework is not in fixture/; the builder must use whatever response type the host app provides

## Decision 1: where CSV serialization lives
- options: a function in app/reports/views.py next to the new view | a new module app/reports/export.py
- forces: 1 caller today and well under 100 lines, so the bar says inline it; move it out only when a second format (XLSX) or a second caller arrives
- door: two-way, a function move
- evidence: traced, counted callers in views.py

## Decision 2: export history is owned by app/reports, not a new exports module or app/users
- options: functions in app/reports/models.py | a new app/exports package
- forces: same-reason test — history changes exactly when export changes (new format, new field), so it has one owner with the export; app/users/models.py only reads users and never needs to know about exports
- door: two-way, internal module boundary
- evidence: traced, read app/users/models.py and app/reports/*

## Move 1: scope get_report to the requesting user
- cost: 1 unscoped query (app/reports/models.py:12) reachable by 1 caller today, 2 once the export view lands
- pays: download one report as CSV — the export view reuses an owner-safe lookup instead of re-implementing the check (0 duplicate checks)
- files: app/reports/models.py:10, app/reports/views.py:9
- owner: app/reports/models.py get_report(report_id, owner_id), query "... WHERE id = ? AND owner_id = ?"
- callers: app/reports/views.py:10 report_detail → get_report(report_id, request.user_id)
- door: two-way, land it and go
- proof: add tests/test_reports.py seeding two users each with one report; `pytest tests/test_reports.py` passes with get_report(a_report_id, owner_id=b) returning None and get_report(a_report_id, owner_id=a) returning the row
- effort: S
- after: nothing

## Move 2: add the CSV download view
- cost: 0 export paths today
- pays: download one report as CSV — lands in 1 file (views.py), 0 new modules
- files: app/reports/views.py
- owner: app/reports/views.py report_export_csv(request, report_id), plus a private _report_to_csv(report) -> str using csv.writer
- callers: new route in the host app's router (not in fixture/), and a "Download CSV" button on the reports page linking to it
- door: two-way, land it and go
- proof: `pytest tests/test_reports.py` passes with: owner gets text/csv, Content-Disposition attachment, and csv.reader round-trips the header row and one data row; non-owner gets 404; a title starting with "=" is written with a leading "'" (spreadsheet formula injection)
- effort: S
- after: Move 1
