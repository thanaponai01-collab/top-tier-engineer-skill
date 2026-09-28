I've written the design to `fixture/docs/arch-design-csv-export.md`. In short: the feature fits inside `app/reports/` with no restructuring. The one choice I need you to confirm is **how export history is stored**, because a stored data shape is hard to change later.

**Before anyone writes the export endpoint:** `get_report(report_id)` at `app/reports/models.py:10` looks a report up by id only and never checks who owns it. If the CSV button is built on it, anyone who knows or guesses a report id can download another user's report. `report_detail` at `views.py:9` already has this gap. I recorded it but left it alone, since fixing it is outside this feature.

## Proposed structure
Three small steps, each one reversible:

1. **Add an owner-checked lookup:** a new `get_report_for_owner(report_id, owner_id)` in `reports/models.py`. `list_reports` already filters by owner the same way.
2. **Put the CSV formatting in its own new file:** a pure function `to_csv(report)` in `app/reports/export.py`, using Python's built-in `csv` module. It should also guard against spreadsheet formula injection (values starting with `=`, `+`, `-` or `@`). Keeping this out of the view means adding a column or an XLSX format later only edits this one file.
3. **Add the export view:** `report_export_csv` in `views.py`. It uses the owner-checked lookup, returns 404 for anyone else's report, and sends the file as a `text/csv` download. The button and route aren't in `fixture/`, so hook it up wherever `report_detail` is routed.

History goes in `reports/models.py` for now (`record_export` / `recent_exports`), not a new `exports/` package. There's only one thing to export today, so a separate package isn't worth it yet.

## Decision needed: where export history is stored
- **A (my recommendation):** a table `report_exports(id, user_id, report_id, title, exported_at)`. It copies the title at export time, so the history still reads correctly if a report is renamed or deleted. Reads return the newest 10, and nothing is pruned at launch.
- **B:** store only `report_id` and look up the current title when showing history. It's less data, but history would show new titles and lose deleted reports.
- **C:** keep history in the browser's local storage. There's no table, but history is per device and lost when the browser is cleared.
- **Cost of choosing wrong:** a migration plus a backfill that can't recover titles that were never stored. There's also nothing in `fixture/` that creates tables, so tell me where schema changes go and I'll add this as step 4.

## Two product questions
- **Which page has the button?** An export from the report detail page (one report) is a different feature from exporting the report list.
- **What columns go in the CSV?** `body` is a single text field, so do they want id, title, created and body, or does the body contain rows that should become the CSV rows?

## How I checked
- I traced this by reading all four source files. It hasn't been run: nothing is built, and there's no git history to analyse.
- The owner-check gap is simple to see in 14 lines of code. I didn't get a second, independent check on it.
- The doc's own format check can't run inside `fixture/` because it isn't a git repository. It passed with 0 errors on a scratch copy I put under git (`/tmp/archcheck`).
- I skipped the architecture diagram: the change is three additions inside one folder.

<!-- file written by the agent: fixture/docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: no-git (fixture/ is not a repository; analysis is of the working tree on 2026-09-27)
- question: where do "download report as CSV" and "last few exports" (timestamp + title) live in app/, so launch touches few modules and the likely follow-ups stay cheap?
- yardstick: export one report as CSV (today: reports/ only — 2 files); show a user their last N exports (today: reports/ + a new table — 2 files + schema); add a field or format to exports later, e.g. row count or XLSX (after moves: 1 file each)
- status: open
- verdict: clean — four small files, one data-access owner (app/db.py), one owner per concept; the feature fits inside app/reports/ with no restructuring
- context: app/db.execute stays the only DB access path; views keep the existing `view(request, ...) -> render(data)` shape; the export history table is NOT covered by these moves until its shape is confirmed (see answer: parked one-way door)

## Finding 1: get_report does not scope by owner, so an export view built on it would hand any report to any user
- where: app/reports/models.py:10
- cost: 1 existing caller (app/reports/views.py:10, report_detail) reads a report by id with no owner_id check; a CSV endpoint reusing it would be a 2nd unscoped reader and a downloadable IDOR
- badge: strong
- evidence: traced — read models.py:10-14 (WHERE id = ? only) and views.py:9-11 (no check on request.user_id); list_reports at models.py:4 does filter by owner_id, so the pattern exists

## Finding 2: no schema/migration owner in the tree
- where: app/db.py:4
- cost: 0 files create tables; reports and users tables are assumed to exist, so the new export-history table has no obvious home
- badge: worth exploring
- evidence: traced — grep for CREATE across fixture/ returns nothing; the schema lives outside this tree or is hand-managed

## Decision 1: where CSV formatting lives
- options: A) a pure `to_csv(report) -> str` in new app/reports/export.py, called by a thin view | B) build the CSV inline in views.py
- forces: formatting changes for different reasons than HTTP handling (columns, escaping, future XLSX); a pure function is testable without a request; B is fewer files but mixes the two and the yardstick's 3rd change would edit the view
- door: two-way — internal module layout, decide A
- evidence: traced — views.py has only thin passthrough views today; stdlib csv covers quoting, no new dependency

## Decision 2: export history belongs to reports/, not a new app/exports/ package
- options: A) record_export / recent_exports in app/reports/models.py | B) new app/exports/ package
- forces: one feature, one caller, a handful of lines; B earns its place only when a second exportable thing (users, invoices) exists — none does today
- door: two-way — moving two functions to a package later is a mechanical rename
- evidence: traced — only reports/ and users/ exist; users/ has no export requirement

## Move 1: scope report reads by owner
- cost: get_report(report_id) at app/reports/models.py:10 has no owner filter (Finding 1)
- pays: export one report as CSV: can reuse the model read safely instead of writing a 2nd query — 1 file edited, no second read path
- files: app/reports/models.py:10-14
- owner: app/reports/models.py — add get_report_for_owner(report_id, owner_id) with `WHERE id = ? AND owner_id = ?`; leave get_report as is (report_detail's own gap is reported, not fixed here)
- callers: none yet; Move 3's export view is the first
- door: two-way, land it and go
- proof: against a sqlite DB with two users each owning one report, `get_report_for_owner(other_users_report_id, me)` returns None and `get_report_for_owner(my_report_id, me)` returns the row
- effort: S
- after: nothing

## Move 2: pure CSV serializer
- cost: no CSV code exists; without a named owner it lands inside the view (Decision 1)
- pays: add a field or format to exports: 1 file (export.py) instead of editing the view
- files: app/reports/models.py:12
- owner: app/reports/export.py (new file; input is the get_report row shape id/title/created_at/body at models.py:12) — `to_csv(report) -> str` using stdlib csv.writer, header row then data; the column set is the open product question in the answer
- callers: Move 3's export view only
- door: two-way, land it and go
- proof: unit test — a report whose title contains a comma, a quote and a newline round-trips through csv.reader to the same values; a title starting with `=` is prefixed with `'` (spreadsheet formula injection)
- effort: S
- after: nothing

## Move 3: export view and button wiring
- cost: no export endpoint exists; reports/views.py:9 report_detail is the pattern to copy
- pays: export one report as CSV: 2 files (views.py + export.py) plus the route/template, which live outside fixture/
- files: app/reports/views.py:9-15
- owner: app/reports/views.py — `report_export_csv(request, report_id)`: get_report_for_owner → 404 if None → to_csv → response with Content-Type text/csv and Content-Disposition attachment; filename from report id, not raw title
- callers: the reports page button (template/route not in fixture/; wire it where report_detail is routed)
- door: two-way, land it and go
- proof: request as the owner returns 200 text/csv whose body parses to the report's row; request for another user's report_id returns 404
- effort: S
- after: Move 1
