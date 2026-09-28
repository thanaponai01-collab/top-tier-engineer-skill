**Short version:** put all of this inside `app/reports`. You only need one new file, `app/reports/export.py`, plus one new view. `app/db.py` stays the only thing that opens a connection. The one decision that's hard to undo is **the shape of the export-history table**, and I've left it open until you say yes.

The design is in `fixture/docs/arch-design-csv-export.md`. Its check shows 0 broken fields. It does flag one "stale" warning, but only because `fixture/` isn't a git repo, so there's no commit to pin the design to.

## What I found (from reading all 4 files in `fixture/`)
- **The code is small and clean.** There's one data-access function (`db.execute`), and each area has its own `models.py`. The CSV export and a column added to it later can each be done inside the one module.
- **`get_report` doesn't check who owns the report** (`app/reports/models.py:10`). `list_reports` filters by `owner_id`; `get_report` looks up by id only. If the export view is built on it, any user could download any report. `fixture/` has no router or middleware, so a check may exist upstream, but nothing here shows one.
- **CSV can be abused through formulas.** Titles and bodies are text users type. A cell that starts with `= + - @` runs as a formula when opened in Excel or Sheets. The serializer should escape those.
- **There's no UI layer in `fixture/`.** No templates, no routes; `render()` just returns the data unchanged. The button and the URL route will live wherever the real frontend and router are.

## How to structure it (2 moves, both easy to undo)
1. **Add a read that checks ownership:** `get_report_for_owner(report_id, owner_id)` in `models.py`. It filters in SQL the same way `list_reports` already does.
2. **Add the CSV code:** `export.py` with `to_csv(header, rows)`, using Python's built-in `csv` module (no new dependency) and escaping formulas. Then add a `report_export` view that returns it as a `text/csv` attachment. Having one serializer means adding a CSV column later touches one file.

Each move has a runnable proof command written in the file.

## Parked: needs your yes before anyone builds the history
There are no schema or migration files in `fixture/`, so a new table is a change to stored data that you can't cheaply undo. My recommendation:
- **Table:** `report_exports(id, user_id, report_id, report_title, exported_at)`, written by the export view after the CSV is built.
- **Store the title as it was at export time** rather than joining to `reports`. Otherwise renaming or deleting a report rewrites or loses its history entries.
- **Keep every row and show the last few with `ORDER BY exported_at DESC LIMIT 5`** instead of deleting old ones. The "5" can change freely later; rows you've pruned are gone for good.
- **Alternative:** keep the history in the browser (localStorage) with no table at all. It's cheaper, but the history won't follow the user to another device.
- **If this is wrong:** renaming or dropping columns later means a migration, plus a backfill for any rows already written.

## One question for product
Is the CSV **one report** (id, title, created_at, body) or **the list of reports**? The history is described as "the report title", which points to one report per export, and that's what I assumed. The structure is the same either way; only the columns passed to `to_csv` change.

I didn't get a second-opinion check from a subagent, because nothing here rose to a "strong" finding or an approved hard-to-undo decision. Everything above comes from reading the four files.

<!-- file written by the agent: fixture/docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repository; analysis true of the tree on 2026-09-27)
- question: where do a per-report "download as CSV" action and a short per-user export history go?
- yardstick: add CSV export of a report (1 module: app/reports); record + show last N exports (1 module + 1 new table, no schema file exists); add a column to the CSV later (1 file if one serializer owns the columns)
- status: open
- verdict: clean
- context: everything stays inside app/reports; app/db.py stays the only place that opens connections; no new dependency (stdlib csv); the export-history table shape is NOT decided here (parked, needs a yes)

## Finding 1: single-report read is not scoped to its owner
- where: app/reports/models.py:10, app/reports/views.py:9
- cost: 1 of 2 report reads is unscoped (list_reports filters owner_id at models.py:6; get_report filters only id at models.py:12); an export view built on get_report would let any user download any report by id
- badge: worth exploring
- evidence: traced within fixture/ (no middleware or router exists here, so enforcement upstream can't be ruled out)

## Finding 2: CSV output is a formula-injection surface
- where: app/reports/models.py:12
- cost: title and body are user-written text; a cell starting with = + - @ runs as a formula when opened in Excel/Sheets
- badge: worth exploring
- evidence: traced (the columns come straight from the reports table)

## Decision 1: where the CSV serialization lives
- options: A) app/reports/export.py with one to_csv(rows) using stdlib csv, called by a new view | B) inline csv writing inside views.py
- forces: yardstick 3 (add a column) wants one owner of the column list; A has 1 caller today, so it only earns its file because the history write and the escaping also sit next to it — B is fine if product keeps it that small
- door: two-way, internal module layout
- evidence: traced (views.py render() at :14 returns data unchanged; no existing serializer anywhere in fixture/)

## Decision 2: owner check for export goes in the model, not the view
- options: A) add owner_id to the query: get_report_for_owner(report_id, owner_id) in models.py | B) fetch with get_report and compare owner in the view
- forces: list_reports already scopes in SQL (models.py:6), so A matches the existing idiom and B needs owner_id selected too; A also fixes report_detail if it switches over
- door: two-way, internal function
- evidence: traced (models.py:4-14)

## Move 1: scoped read for export
- cost: get_report has no owner filter (models.py:12)
- pays: CSV export and later report_detail share one scoped read: 0 new query sites in views
- files: app/reports/models.py:10
- owner: app/reports/models.py get_report_for_owner(report_id, owner_id)
- callers: new report_export view (Move 2); report_detail at app/reports/views.py:10 may switch later, not required
- door: two-way, land it and go
- proof: seed a sqlite reports table with report 1 owned by user 1; `python -c "from app.reports.models import get_report_for_owner as g; print(g(1,1) is not None, g(1,2) is None)"` from fixture/ prints `True True`
- effort: S
- after: nothing

## Move 2: CSV serializer and export view
- cost: no CSV path exists; render() at views.py:14 is the only output
- pays: add a CSV column later: 1 file (export.py column list)
- files: app/reports/views.py:14
- owner: new app/reports/export.py to_csv(header, rows) -> str (stdlib csv, prefixes ' to cells starting with = + - @); new view report_export(request, report_id) in views.py returns it with Content-Type text/csv and Content-Disposition attachment
- callers: report_export only; the button and URL route live outside fixture/ (no router or template exists here)
- door: two-way, land it and go
- proof: `python -c "from app.reports.export import to_csv; print(to_csv(['id','title'], [(1,'=SUM(A1)')]))"` from fixture/ prints a header line `id,title` and `1,'=SUM(A1)`
- effort: S
- after: Move 1
