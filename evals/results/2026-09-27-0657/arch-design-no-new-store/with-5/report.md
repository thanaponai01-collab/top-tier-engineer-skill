I'd build this entirely inside `app/reports`, with no new package or abstraction. But first `get_report` needs to check who owns the report. Right now `report_detail` returns any report to any logged-in user who knows its id. If we put a download button on top of that, anyone can download anyone's report.

The hardest decision to undo is the new database table for export history. That's a stored data shape, so I've left it out of the moves until you agree on it (below).

**Proposed structure**
- **Where the code goes.** `get_report` in `app/reports/models.py` also filters by `owner_id`. `app/reports/views.py` gets:
  - `report_to_csv(report)`, which uses Python's built-in `csv` module;
  - a `report_export` view;
  - a `render_csv` helper next to `render`, which marks the response as a CSV file download.
- **History queries** go in `app/reports/models.py`: `record_export(...)` and `recent_exports(user_id, limit=5)`.
- **Why not a separate `exports` package:** exports change whenever report fields change, so they belong with reports. A separate package would have one caller and under 100 lines. I'm also not adding a pluggable exporter for other formats, because only CSV exists.
- **Spreadsheet formula risk:** titles and bodies are written by users. A cell starting with `=`, `+`, `-` or `@` runs as a formula in Excel, so the export should put a `'` in front of it.

**One question before the table: is a history row a snapshot of the title, or a link to the report?** I recommend storing both. Table `report_exports`, one row per export:
- `id`
- `user_id`
- `report_id`
- `report_title` (copied at export time)
- `exported_at` (UTC)
- an index on (`user_id`, `exported_at` descending)

The history then shows the title the user actually exported, even if the report is later renamed or deleted. Launch only reads the latest 5 rows, and nothing gets deleted.

If we get this wrong, fixing it later means a data migration. There's also a wrinkle: nothing in `fixture/` creates or migrates any table, so this would be the first schema code in the repo. Where do the existing `reports` and `users` tables get created?

**Assumptions to confirm**
- I've read "download as CSV" as one report per export. The history spec, one title per export, points that way. If it means exporting the whole list, the history row needs a different shape.
- `render` just returns its input unchanged, and I can't see what web framework sits behind it. Setting the file-download headers depends on that framework.

**Evidence:** the ownership gap and the missing schema code come from reading all four files in `fixture/`, and a separate check agreed. The only call to `get_report` is at `app/reports/views.py:10`, with no owner check, and no file creates or alters a table. There's no git history, so the design rests on reading the code and on your request, not on past change patterns. I didn't draw a diagram because it's only four files and two moves.

**Plan file:** `fixture/docs/arch-design-report-export.md`. It holds the two findings, two decisions and two moves:
1. Make `get_report` check the owner.
2. Add the CSV download.

Each move lists the test that proves it works. The skill's `check` script finds no broken fields or file references. It still fails on one item: the file can't be pinned to a commit because `fixture/` isn't a git repo. Separately, the script only resolves file paths correctly without git when the plan file sits at the project root, so I checked a temporary copy there. Once you answer the table question, I'll add the history move to the file.

<!-- file written by the agent: fixture/docs/arch-design-report-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo; analysis true of the working tree on 2026-09-27)
- question: where do "download report as CSV" and "last few exports (timestamp + title)" live in fixture/app, and what must change first?
- yardstick: export one report as CSV (touches 1 module: app/reports); show a user's recent exports (1 module + a new table, no schema home exists); add a field or format to the export later (1 module if the serializer is a single function)
- status: open
- verdict: clean
- context: reading = one export is one report (history row carries that report's title); app.db.execute stays the only query path; the HTTP framework behind `render` is unknown and is not changed here; the export-history table is parked until its shape is confirmed (see chat)

## Finding 1: report_detail returns any report to any user
- where: app/reports/views.py:10
- cost: 1 of 1 call sites of get_report skips an owner check; get_report filters by id only (app/reports/models.py:12). A CSV endpoint built on it turns this into a one-click download of anyone's report.
- badge: strong
- evidence: traced, read both files; subagent recount (not told the conclusion) found the same 1 call site with no owner check

## Finding 2: no home for schema changes
- where: app/db.py:4
- cost: 0 files create or migrate tables; the export-history table would be the first schema written in this repo
- badge: worth exploring
- evidence: traced, grep for CREATE/ALTER/migration found none; subagent confirmed

## Decision 1: where the export code lives
- options: inside app/reports (serializer + view in views.py, history queries in models.py) | new app/exports package
- forces: exports change when the report's fields change (same reason as reports) → one owner; a new package would have one caller and < 100 lines
- door: two-way
- evidence: traced, app has 2 feature packages (reports, users), each models.py + views.py

## Decision 2: CSV serializer shape
- options: one function report_to_csv(report) in views.py using stdlib csv | a pluggable exporter interface for future formats
- forces: one format at launch; an interface would have 1 implementation; stdlib csv covers quoting. Cells starting with = + - @ must be prefixed with ' (spreadsheet formula injection from user-written titles/bodies)
- door: two-way
- evidence: traced, get_report returns (id, title, created_at, body) at app/reports/models.py:12

## Move 1: scope get_report to its owner
- cost: any user can read any report by id (Finding 1)
- pays: export one report as CSV, safe to build on get_report without a second check
- files: app/reports/models.py:10, app/reports/views.py:10
- owner: get_report(report_id, owner_id) in app/reports/models.py, adding `AND owner_id = ?`
- callers: app/reports/views.py:10 (report_detail) passes request.user_id
- door: two-way, land it and go
- proof: a test with two users: user B calling report_detail on user A's report gets None / not-found; user A still gets the row
- effort: S
- after: nothing

## Move 2: add the CSV download
- cost: feature does not exist
- pays: export one report as CSV, lands in 1 module (app/reports)
- files: app/reports/views.py:14
- owner: report_to_csv(report) -> str and report_export(request, report_id) in app/reports/views.py; a render_csv(text, filename) beside render() sets Content-Type text/csv and Content-Disposition attachment
- callers: new route for report_export; the reports page button links to it
- door: two-way, land it and go
- proof: test that report_to_csv on a row with a comma, quote, newline and a leading "=" in the title round-trips through csv.reader with the "=" cell prefixed by '; test report_export for another user's report returns not-found
- effort: S
- after: Move 1
