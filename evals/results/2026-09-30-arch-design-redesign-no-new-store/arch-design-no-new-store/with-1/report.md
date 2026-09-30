**Verdict: `fixture/` is clean, and this fits without restructuring.** Put the CSV logic and the history inside `app/reports/`, and fix one auth gap before adding the export route. The design is in `docs/arch-design-report-export.md`, and its checker exits 0 (0 broken, 0 stale). I only read code and wrote that file.

**Structure**
- **`reports/export.py` (new):** a pure `to_csv(rows, header) -> str` using the stdlib `csv` module. It prefixes cells starting with `= + - @` so spreadsheets don't run them as formulas. It touches no database, so it can be tested with plain lists.
- **`reports/models.py`:** add `record_export(user_id, report_id, title)` and `list_exports(user_id, limit)`, both using `app.db.execute`. History changes for the same reasons as reports, has one caller, and would be under 30 lines. A separate `exports` package would be a seam with one user.
- **`reports/views.py`:** a `report_export` view that fetches the report, calls `to_csv`, records the export and returns the file. `report_list` also passes in the recent history.

**Moves, in order**
1. **Scope `get_report` to the owner** (`models.py:10`). It takes only `report_id`, while `list_reports` filters by `owner_id`. An export route built on it would let any user download any report. This is *traced* (I read the code) but not run, because the fixture has no schema or runnable app. Size S.
2. **Add `export.py`** with tests for escaping and the formula guard. Size S.
3. **Add the export view, the history functions and the button.** It depends on moves 1 and 2. Size M.

**Parked: needs a yes from you.** The `exports` table shape is stored data, so I left it out of the file. Nothing in `fixture/` declares any table (I grepped for `CREATE TABLE` and found nothing), so I don't know how schema changes ship. My recommendation:
- **Columns:** `exports(id, user_id, report_id, report_title, exported_at)`.
- **Title:** store the title as a snapshot, so history still reads correctly if a report is renamed or deleted.
- **Cost if wrong:** a backfill.

I need two answers before move 3:
- Where do migrations live?
- Does "download as CSV" mean **one report** or the **whole reports list**? I assumed one report, since history records a report title. A whole-list export changes the view and what a history row means.

I also didn't check the reports page template, because it isn't in `fixture/`. Check it before landing move 3, since the button goes there.

**What I could not measure**
- There is no git history, so hidden coupling and hotspots are unmeasured.
- The yardstick (adding a CSV column, changing how many history rows show, adding another format) comes only from the product request.

<!-- file written by the agent: docs/arch-design-report-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo; no history, so change-map was not run)
- question: where do CSV export and a short export history go in fixture/, before anyone writes code?
- yardstick: add a column to the CSV (0 modules today, 1 after: reports/export.py); change how many history rows show (0 today, 1 after: reports/models.py); add a second export format, e.g. XLSX (0 today, 1 after: reports/export.py). Source: the product request only; no git log or tracker to read.
- status: open
- verdict: clean
- context: reports keep their own models/views pair; app/db.py stays the only place that opens a connection; the request/auth model (`request.user_id`) stays.

## Finding 1: report_detail has no owner check, so an export-by-id route would leak other users' reports
- where: fixture/app/reports/models.py:10
- cost: 1 of 2 report reads is unscoped (get_report takes only report_id; list_reports at line 4 filters by owner_id). Any user_id can read any report through it.
- badge: strong
- evidence: traced, read models.py and views.py end to end; views.py:9-11 passes only report_id. Not run (no runnable app or schema in the fixture).

## Finding 2: no schema or migration owner exists for a new table
- where: fixture/app/db.py:1
- cost: 0 CREATE TABLE statements in fixture/ (grep), yet 3 queries read `reports` and `users`. The history table has nowhere to be declared.
- badge: worth exploring
- evidence: proven, grep for "CREATE TABLE" over fixture/ returned nothing.

## Decision 1: where the CSV logic lives
- options: pure function `to_csv(rows) -> str` in a new reports/export.py, called by the view | build the CSV inline in the view
- forces: the view has one caller and no logic today; CSV escaping and spreadsheet formula injection (cells starting `=`, `+`, `-`, `@`) is real logic that wants a test with no database. A pure function tests with a list of tuples.
- door: two-way
- evidence: traced, views.py:1-15 and models.py:1-14 show no existing formatting code to reuse.

## Decision 2: where export history lives
- options: history functions inside reports/models.py, using app.db.execute | a new top-level `exports` package
- forces: history changes for the same reason as reports (report fields, owner scoping), has one caller, and would be under ~30 lines. A new package is a seam with one user.
- door: two-way
- evidence: traced, db.py is the single query entry point and both existing models modules use it directly.

## Move 1: scope report reads to the owner
- cost: get_report(report_id) at models.py:10 has no owner filter; the new export route would be the second route to read by bare id.
- pays: add the export route safely: 0 extra auth code in the export view, because the model refuses a foreign id.
- files: fixture/app/reports/models.py:10-14; fixture/app/reports/views.py:9-11
- owner: reports/models.py, `get_report(report_id, owner_id)` adds `AND owner_id = ?`
- callers: views.py:10 (report_detail). Re-grep `get_report` before landing.
- door: two-way, land it and go
- proof: a test that user B calling get_report on user A's id returns None; run with pytest, expect pass. Replaces no old tests (none exist).
- effort: S
- after: nothing

## Move 2: add the pure CSV formatter
- cost: none today; this is the new job's owner.
- pays: add a CSV column: 1 file (reports/export.py).
- files: fixture/app/reports/models.py:1 (sibling; export.py is created next to it)
- owner: reports/export.py, `to_csv(rows, header) -> str`, using the stdlib `csv` module and prefixing a `'` to cells that start with `= + - @`
- callers: the new export view only
- door: two-way, land it and go
- proof: pytest on to_csv: commas, quotes, newlines round-trip through `csv.reader`; a cell `=1+1` comes out neutralised. Expect pass.
- effort: S
- after: nothing

## Move 3: export view and button, then history read
- cost: none today.
- pays: change how many history rows show: 1 file.
- files: fixture/app/reports/views.py:4-15; fixture/app/reports/models.py:14
- owner: views.py orchestrates (get_report → to_csv → record_export → respond); models.py owns the history SQL
- callers: the reports page template (not in fixture/; check it before landing)
- door: two-way, land it and go
- proof: a test with a temp sqlite DB via app.db.DB_PATH: export twice, list_exports(user, limit=5) returns 2 rows newest first with title and timestamp; a foreign report id exports nothing and records nothing.
- effort: M
- after: Move 1, Move 2
