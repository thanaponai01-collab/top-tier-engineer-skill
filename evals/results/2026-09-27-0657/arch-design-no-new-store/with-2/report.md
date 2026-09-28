Put all of it inside `app/reports`. The CSV part is small and can start now. The history part needs a new database table, and that's the one decision that's hard to undo later, so I've held it back until product answers the questions below.

## Structure

- **`app/reports/export.py`** (new): one function, `report_to_csv(report) -> str`, using Python's built-in `csv` module. It's the only place that knows the CSV format and it doesn't touch the database or the request. Adding a column or a second format later changes only this file.
- **`app/reports/views.py`**: a new `report_export_csv(request, report_id)` view. It looks up the report as the current user, builds the CSV, records the export, and returns the file.
- **`app/reports/models.py`**: all SQL stays here and goes through `app/db.py:execute`, like the existing queries. The history will need two new functions: `record_export(...)` and `list_recent_exports(user_id, limit)`.
- No new top-level module. With one caller, a separate `exports/` package doesn't pay for itself.

## Something to fix before building (traced)

`get_report` (`app/reports/models.py:10`) looks a report up by id only. It doesn't check who owns it, so `report_detail` will return any user's report. A CSV export built on it would let any user download any report. The fix is to have `get_report` take an `owner_id` and filter on it, the way `list_reports` already does. It has exactly one caller today (`views.py:10`, recounted with grep). This also changes the detail page: it will stop returning other users' reports. That's a fix, but it is a change people will notice.

## Needs a yes: the export history table

Once rows are stored, changing their shape means migrating data, so I'd like confirmation first.

- **Option A (recommended):** a table `report_exports(id, user_id, report_id, title, exported_at)`. The page shows the newest 5 with `ORDER BY exported_at DESC LIMIT 5`, and nothing gets deleted at launch.
  - `title` is a copy taken at export time, so the history still reads correctly if a report is renamed or deleted.
  - `report_id` is kept so we can link back later.
- **Option B:** keep the history in the browser (localStorage). No schema change, but it's lost across devices and browsers.
- **If we pick wrong:** choosing A and then wanting B costs one unused table. Choosing B and then wanting A means the history users already built up can't be moved over.

**Questions for product/eng:**
1. What goes in the CSV? A report has a single `body` field. Is the CSV one row (`id,title,created_at,body`), or is `body` really table data we should split into rows?
2. How are tables created? `fixture/` has no migrations and no `CREATE TABLE`, and `render()` just passes data through, so I couldn't see how headers or file downloads are returned. That's outside what I was given.

## The file

`fixture/docs/arch-design-report-export.md` has two findings, two decisions, and two small moves ready to build: (1) make `get_report` check the owner, (2) add the CSV view. Each has a proof command. The history move will go in once the table is approved.

**`check` exits 1.** Every failure comes from `fixture/` not being a git repo: the checker can't pin a commit or resolve paths, and it also flags the not-yet-created `export.py`. I checked every cited `file:line` by hand against the source instead. If you run `git init` and commit in `fixture/`, I can pin `at:` and get a clean check.

I skipped the git-history analysis (there's no history) and the subagent second opinion, because the whole codebase is 4 files and the key count was confirmed with grep.

<!-- file written by the agent: fixture/docs/arch-design-report-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo; true of the files as read 2026-09-27)
- question: where do "download report as CSV" and a per-user "recent exports" list live in fixture/app?
- yardstick: export one report as CSV (touches 1 module: app/reports); show a user their last few exports with timestamp + title (touches 1 module: app/reports, plus a new table); add a second format or history field later (assumed next change, not from product; touches 1 file: app/reports/export.py)
- status: open
- verdict: clean
- context: SQL goes only through app/db.py:execute; the export lives inside app/reports (no new top-level module); the export-history table is NOT designed here yet — it is a one-way door parked for product (see chat)

## Finding 1: report lookup is not scoped to the owner
- where: app/reports/models.py:10
- cost: 1 of 1 callers (app/reports/views.py:10) returns any report by id to any user; a CSV export built on get_report inherits it
- badge: strong
- evidence: traced, get_report SELECTs by id only (models.py:12) while list_reports filters on owner_id (models.py:6); report_detail passes no user (views.py:10)

## Finding 2: no response or schema pattern exists to follow
- where: app/reports/views.py:14
- cost: render() returns data unchanged; no content-type/header path, no migrations or CREATE TABLE anywhere in fixture/
- badge: worth exploring
- evidence: traced, grep for CREATE/render/csv over fixture/ finds only views.py:14

## Decision 1: where CSV formatting lives
- options: pure function report_to_csv(report) -> str in new app/reports/export.py | inline csv writing in the view
- forces: the likely next change is another format or column, which should touch one file with no request object; one caller today argues for inline
- door: two-way
- evidence: traced, views.py has no helpers beyond render; stdlib csv covers it, so no dependency

## Decision 2: how the export checks ownership
- options: get_report(report_id, owner_id) filters on owner_id and report_detail passes request.user_id | separate get_owned_report used only by export
- forces: one lookup keeps one owner of "fetch a report"; changing get_report also changes report_detail to return None for other users' reports (a behavior change, but it fixes Finding 1)
- door: two-way
- evidence: traced, get_report has exactly one caller (views.py:10)

## Move 1: scope get_report to its owner
- cost: Finding 1, 1 unscoped caller
- pays: export one report as CSV: can reuse the lookup safely instead of adding a second query
- files: app/reports/models.py:10, app/reports/views.py:9
- owner: app/reports/models.py:get_report
- callers: app/reports/views.py:10 (report_detail) becomes get_report(report_id, request.user_id)
- door: two-way, land it and go
- proof: with a sqlite db holding report 1 owned by user 1, `python -c "from app.reports.models import get_report; print(get_report(1, 2), get_report(1, 1) is not None)"` prints `None True`
- effort: S
- after: nothing

## Move 2: add the CSV export view
- cost: feature does not exist
- pays: export one report as CSV: 1 module (app/reports: export.py new, views.py edited)
- files: app/reports/export.py (new), app/reports/views.py:9
- owner: app/reports/export.py:report_to_csv owns the CSV format; views.py:report_export_csv owns the request
- callers: new route for report_export_csv wired wherever report_detail is routed (router not in fixture/)
- door: two-way, land it and go
- proof: `python -c "from app.reports.export import report_to_csv; print(report_to_csv((1,'Q3','2026-09-01','x,y')))"` prints a header `id,title,created_at,body` and one row with the body quoted as `"x,y"`; the view returns 404 for a report owned by another user
- effort: S
- after: Move 1
