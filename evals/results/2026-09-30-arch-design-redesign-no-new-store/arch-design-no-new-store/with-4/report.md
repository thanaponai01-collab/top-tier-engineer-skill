**Verdict: the structure is clean, so add this inside `app/reports` and don't create a new package.** I wrote the plan to `docs/arch-design.md`, and its `check` exits 0. Nothing is built.

**One bug to fix first.** `get_report` has no owner check (`reports/models.py:10`). `list_reports` filters by `owner_id`, but `get_report` fetches by id alone. An export view built on it would let any user download any other user's report body. This is *traced*: I read all four files. Move 1 scopes `get_report` to its owner.

**Structure (Move 2):**
- **`reports/export.py` (new):** a pure `to_csv(report)` built on the stdlib `csv` module. It stops spreadsheet formula injection by prefixing cells that start with `= + - @`. It needs no database, so it tests directly.
- **`reports/models.py`:** add `record_export(owner_id, report_id, title, now)` and `list_exports(owner_id, limit=5)`. The clock is passed in, not read inside. The history row stores the title as it was at export time.
- **`reports/views.py`:** a new `report_export` view does the owner-scoped fetch, builds the CSV, records the export and returns it as an attachment. `report_list` also passes `list_exports(...)` so the page can show the history.
- **Not chosen:** a separate `exports` package. It would have one caller and under 100 lines, and the history is read on the reports page anyway.

**Parked, needs a yes:** the history needs a new table, for example `report_exports(id, owner_id, report_id, title, exported_at)`. That changes stored data, which is a one-way door. `fixture/` has no schema file or migrations, so I couldn't check how tables get created. I left it out of the file. Please confirm the table shape and who runs the migration.

**Question for Product:** does the button export one report or the whole list? I assumed one report, because the history stores a "report title". This is *suspected*, inferred from the wording. If it's the whole list, only the CSV columns and the history label change.

**Limits of this run:**
- There is no git history, tracker or tests, so the "likely next changes" come from the request alone.
- `fixture/` has no router, and `render` just returns its argument. The route and the button markup go wherever the real app registers views.
- I read the four files and didn't run the import-graph or change-map scripts. With four files, that seemed unlikely to add anything.

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: none (no git repo; analysis true of the 4 files under fixture/app as read 2026-09-30)
- question: where do "download report as CSV" and a short export history go in fixture/app?
- yardstick: add CSV export (views.py + reports/models.py today, 2 modules); add a column to the export (same 2); show more in history, e.g. who/when (same 2). Source: the product request only; there is no git history, tracker or tests to mine.
- status: open
- verdict: clean
- context: reports stay in app/reports; app/db.py stays the only place that touches sqlite; no new package, framework or dependency; exports are per single report (see Decision 2).

## Finding 1: get_report has no owner check, so an export-by-id would leak any user's report body
- where: fixture/app/reports/models.py:10
- cost: 1 call site (views.py:10), 0 owner checks; list_reports filters by owner_id (models.py:6) but get_report does not (models.py:12)
- badge: strong
- evidence: traced, read models.py and views.py end to end. A new export view that calls get_report(report_id) inherits the gap, and exports the full body.

## Decision 1: where the export code lives
- options: new app/exports package with its own models/views | add to app/reports (a pure csv function plus two history functions)
- forces: 1 new caller, under ~100 lines, no second implementer; the history is about reports and is read on the reports page.
- door: two-way
- evidence: traced, read all four files. Adopt the second option.

## Decision 2: export scope (assumed, needs one answer from Product)
- options: one report per click (history row = that report's title) | the whole list per click (history row = a fixed label)
- forces: "report title" in the history only makes sense for a single report.
- door: two-way
- evidence: suspected, inferred from the request wording.

## Move 1: Scope get_report to its owner
- cost: 1 call site with no owner check (views.py:10); an export would add a second
- pays: add CSV export: no cross-user read, so the new view needs no ad-hoc check of its own
- files: fixture/app/reports/models.py:10, fixture/app/reports/views.py:10
- owner: reports/models.py get_report(report_id, owner_id)
- callers: report_detail (views.py:10), plus the new export view
- door: two-way, land it and go
- proof: a test that opens user A's report as user B and gets None (fails before, passes after); the existing owner's read still returns the row
- effort: S
- after: nothing

## Move 2: Add the CSV download, with the history recorded in the same handler
- cost: 0 today; the change touches 2 modules (views.py, reports/models.py) plus 1 new pure function file
- pays: add a column to the export: 1 file (export.py); show more in history: 1 file (models.py)
- files: fixture/app/reports/views.py:9, fixture/app/reports/models.py:10
- owner: new fixture/app/reports/export.py to_csv(report) -> str, pure, stdlib csv module, cells starting with = + - @ are prefixed with ' to block spreadsheet formula injection; models.py record_export / list_exports(owner_id, limit=5); views.py report_export(request, report_id) does get_report (Move 1) -> to_csv -> record_export(owner_id, report_id, title, now) -> response with Content-Disposition attachment; report_list also passes list_exports
- callers: the router (none exists in fixture/, so the route is added wherever the app registers views), and report_list (views.py:5)
- door: two-way for the function layout; the history table is a one-way door and is parked (see the answer)
- proof: unit tests on to_csv (quoting, commas, newlines, a title of =cmd() comes out neutralised) with no database; one test of report_export with now injected and DB_PATH pointed at a temp file, asserting the body, the header and one history row
- effort: M
- after: Move 1
