**Verdict: the code is clean.** Add the CSV export as one small function plus one view inside `reports/`. The export history needs a new stored table, which is a one-way decision. I've left it out of the file until someone says yes.

I wrote the design to `fixture/docs/arch-design-csv-export.md`, and its `check` exits 0. I read all four files under `fixture/app`. There is no git history in `fixture/`, so the only measure was walking each change through the code.

**Structure**
- **CSV writer:** a new `app/reports/csv_export.py` holds a pure function from rows to CSV text, using stdlib `csv`. It has no I/O and no clock.
  - It must neutralize cells that start with `=`, `+`, `-` or `@`, so a report title can't inject a spreadsheet formula.
  - Don't build an exporter interface. Only one format is asked for, and a seam needs two implementers.
- **View:** a new `report_export(request)` in `views.py`, next to `report_list`. It calls `list_reports(request.user_id)`, which is already scoped to the owner, and then the writer.
- **Cost of later changes:** adding a column touches 2 modules, the `SELECT` and the writer. The export itself touches 3.
- **History:** a small `app/reports/exports.py` beside the reports code, with a `record_export` write and a `list_exports` read. It stores timestamp and report title. Keep it in `reports/`, not a new package.

**Things to know**
1. **`get_report` has no owner check** (`app/reports/models.py:10`, called from `views.py:9`). If the export reuses it, anyone can export any report by id. Have the export go through `list_reports`, or add the owner filter first. This is *traced*.
2. **Each `db.execute` opens, commits and closes its own connection** (`app/db.py:11`). "Generate the export" and "record the history" can't share a transaction. The risk is a history row for an export that failed. Record the row after the CSV is built. This is fine for launch.
3. **No download machinery in the fixture.** `render` (`views.py:14`) just returns its data, and there is no HTTP framework. Setting the download headers is unresolved until we know the real framework.

**Parked, needs a yes**
- **History table shape (one-way door).** Options:
  - A. New table `report_exports(id, user_id, report_id, report_title, exported_at)`, with the title stored at export time. I recommend this. It reuses `db.py` and the history stays accurate if a report is later renamed.
  - B. Store only `report_id` and join for the title. That is smaller, but old history rows change when a title is edited.
  - C. Keep history in the browser. It needs no schema, but it is per-device and lost on clear.
- **Schema location.** The fixture has no `CREATE TABLE` or migrations, so I couldn't confirm where the schema lives or how a table gets added. That has to be settled before A becomes a move.

**One question that changes the work**
Does the button export the list of reports (`id, title, created_at`), or one report's contents? The history line "report title" suggests one report per export. `get_report` also returns a free-text `body`, and I don't know how that maps to CSV columns. I designed Move 1 around the list, which is the case that works with the existing code. If it's a single report, the writer's input and the owner check both change.

The file holds one move (the owner-scoped CSV export, effort S) and two findings. It also has one decision (a plain function, not an exporter interface). I didn't draw a diagram, because there is only one move.

<!-- file written by the agent: fixture/docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: no-git (fixture has no repository; analysis true of the 4 files read this session)
- question: where do a "download as CSV" button and a last-few-exports history go in fixture/app?
- yardstick: add CSV export (reports/views.py + reports/models.py + new csv code: 3 modules); add a column to the report table/export (reports/models.py:6 and the CSV writer: 2 modules); show export history (new table + new query + view: 3 modules). Source: the request; no git history or tracker to mine.
- status: open
- verdict: clean
- context: db.py stays the only owner of connections and queries; reports/ stays the owner of report data; the auth model (request.user_id) stays as is

## Finding 1: report_detail reads by id with no owner check
- where: app/reports/views.py:9
- cost: 1 of 2 read paths (get_report, models.py:10) is not scoped to the owner; list_reports (models.py:4) is. An export that reuses get_report exports anyone's report by id
- badge: strong
- evidence: traced, read views.py, models.py and db.py end to end; no other caller exists in fixture/

## Finding 2: every db.execute opens, commits and closes its own connection
- where: app/db.py:11
- cost: 2 writes (generate export, record history) cannot share a transaction; 0 callers need that today
- badge: speculative
- evidence: traced, db.py:11-18

## Decision 1: where the CSV is built
- options: one function in reports/ that turns rows into CSV text using stdlib csv | a pluggable exporter interface (CSV/XLSX/JSON)
- forces: only CSV is asked for (0 second formats); a seam needs 2 implementers today
- door: two-way
- evidence: traced, requirement is a single CSV button

## Move 1: Owner-scoped CSV export, no storage
- cost: today no export exists; the only single-report read (models.py:10) is unscoped
- pays: add CSV export: 3 modules, and later "add a column": 2 modules (the SELECT and the writer)
- files: app/reports/models.py:4, app/reports/models.py:10, app/reports/views.py:4
- owner: app/reports/csv_export.py, a pure function rows -> CSV string. Use stdlib csv. It neutralizes cells starting with = + - @ (spreadsheet formula injection). No I/O, no clock
- callers: one new view `report_export(request)` in views.py, next to report_list; it calls list_reports(request.user_id) then the writer, and returns the download response
- door: two-way, land it and go
- proof: a unit test feeds rows containing a comma, quote, newline and a cell "=1+1" and asserts the exact CSV text (formula cell prefixed with '); a second test asserts another user's report id yields nothing. Both new; no old tests exist
- effort: S
- after: nothing
