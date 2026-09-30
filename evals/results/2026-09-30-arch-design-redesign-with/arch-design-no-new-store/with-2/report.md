**Verdict: the fixture is clean. Build the CSV export as one small pure function plus one view, with no new layer. The export history is parked until you confirm one thing: the shape of its new table.**

The design is written to `docs/arch-design.md`, but its `check` does not pass. `fixture/` is not a git repo, so the checker rejects the `at:` field and the file paths as "not in the repo". The content is hand-verified against the four files I read in full, and I'm not going to force the checker green.

**Structure**
- **`reports/csv_export.py` (new):** a pure `to_csv(header, rows) -> str` using stdlib `csv`, with no db or request access. It has one caller, so there is no exporter class or format registry.
- **`reports/views.py`:** add `report_export(request, report_id)`. It loads the report, builds the CSV, and returns it as a download.
- **`reports/models.py`:** report queries stay here.
- **Neighbouring edits:** `get_report` needs an owner filter, and `report_detail` (`views.py:10`) must pass `request.user_id` to it.
- **Spreadsheet formula injection:** `to_csv` should neutralise cells starting with `=`, `+`, `-` or `@`, because titles and bodies are user-authored. I'm recommending this from general knowledge, so it is *suspected*, not checked against anything in the repo.

**Two findings**
- **Unscoped read (strong, traced):** `get_report` (`models.py:10`) filters by id only, while `list_reports` filters by owner. An export built on it would let any user download any report body, so the owner filter is a prerequisite. It has one caller, so the fix is small.
- **No page for the button (worth exploring, traced):** `render` (`views.py:14`) just returns its argument, and `fixture/` has no template or router. The button itself lives outside what was given, so I can only design the endpoint it calls.

**Parked, needs a yes**
- **History table:** the history needs a new table, and there is no schema or migration mechanism in `fixture/`. Stored data shape is a one-way door, so I left it out of the file.
- **My recommendation:** `exports(id, user_id, report_id, report_title, exported_at)`, showing the last 5 per user.
- **Why the title is stored:** it is a snapshot, so a later rename or delete doesn't change past history.
- **How it would be built:** `record_export` and `recent_exports` in a `reports/exports.py`, called from `report_export`, and the list view would show them.

**One question** that changes the work: does "download as CSV" export the report list, or a single report? The history's "report title" implies per-report, which is how I designed it. If you meant the list, only the `to_csv` inputs change.

**Not checked**
- There is no git history, so change coupling and hotspots are unmeasured.
- The repo has no tests, so Move 1 includes writing them. Its proof is a foreign-owner test that fails before the change and passes after.

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: no-git
- question: where does "download as CSV" plus a short export history (timestamp + report title) go in fixture/app?
- yardstick: add a CSV export (touches 2 modules now if written naively: reports/views.py, reports/models.py); add a column to the export (would touch 1-2); show the last N exports on the reports page (2-3 modules: views, a new table, db)
- status: open
- verdict: clean
- context: sqlite via fixture/app/db.py stays the only data access; `reports` stays one package; the auth model (request.user_id) stays; no new dependencies (stdlib `csv`).

## Finding 1: report_detail reads any report by id, with no owner check
- where: fixture/app/reports/models.py:10
- cost: get_report has 1 caller (views.py:10) and filters by id only; list_reports (models.py:4-7) filters by owner_id. An export endpoint built on get_report would hand any user any report body, 1 unscoped query behind 1 new route.
- badge: strong
- evidence: traced, read models.py and views.py whole; grep shows get_report at views.py:10 and models.py:10 only. No tests exist to say it is intended.

## Finding 2: render is a passthrough, so the fixture has no page for a button
- where: fixture/app/reports/views.py:14
- cost: render returns its argument (1 function, 2 callers, views.py:6 and :11); there is no template, route table or response type in fixture/. The button's home is outside what was given.
- badge: worth exploring
- evidence: traced, read views.py whole; grep finds no template or router in fixture/.

## Decision 1: where CSV generation lives
- options: pure function `to_csv(header, rows) -> str` in `app/reports/csv_export.py`, called by the view | a generic exporter class or plugin registry keyed by format
- forces: one format (CSV), one caller, about 15 lines with stdlib `csv`; a registry needs a second format to pay for itself.
- door: two-way, adopt the function; it takes no db and no request, so it tests with a list of tuples.
- evidence: traced, from the 4 files read; no second format appears in the requirement.

## Decision 2: guard against spreadsheet formula injection in cells
- options: prefix cells starting with `=`, `+`, `-`, `@` with `'` inside to_csv | export raw and leave it to the consumer
- forces: title and body are user-authored and the file opens in Excel or Sheets for the person who downloads it.
- door: two-way, one function's behavior.
- evidence: suspected, general CSV-injection knowledge; nothing in fixture/ handles it. Recommendation: escape.

## Move 1: scope get_report by owner, add the CSV export view
- cost: no export path exists; the only single-report read (models.py:10) is unscoped, Finding 1
- pays: add the export: 2 modules touched (reports/views.py, reports/csv_export.py) instead of 3-plus with an ad hoc query; add an export column: 1 module (csv_export.py)
- files: fixture/app/reports/models.py:10-14 (get_report takes owner_id and adds `AND owner_id = ?`); fixture/app/reports/views.py:9-11 (report_detail passes request.user_id) and a new report_export view beside it; new fixture/app/reports/csv_export.py (pure `to_csv`)
- owner: csv_export.py owns the CSV format; models.py owns report queries
- callers: get_report has 1 call site, views.py:10; to_csv has 1 new caller, report_export
- door: two-way, land it and go
- proof: no tests exist, so the move adds them: `pytest fixture` with (a) to_csv of `[("=1+1", "a,b")]` gives a header row plus one escaped row; (b) get_report(other user's id) returns None; (c) report_export for a foreign report returns not-found. Green after, and (b) and (c) fail before. Replaces no old tests.
- effort: S
- after: nothing
