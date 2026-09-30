Put a per-report CSV export and a small export history in `app/reports/`, as two moves that land in order. The design is written to `fixture/docs/arch-design.md`. No code has been written.

The checker passes (0 broken, 0 stale) on a throwaway git copy. On `fixture/` itself it fails, because it's not a git repo and the checker needs a commit to pin `at:` to. The `at:` line says `no-git`. Running `git init` there would make it pass, but I didn't touch your tree.

`fixture/` is four small files with no git history. The yardstick comes from your request: add or rename a CSV column, change what the history shows or how many rows, and add a second export format. Counts in the file are traced from reading the code, not measured.

**Structure**
- **Move 1 – CSV export:**
  - A new `app/reports/csv_export.py` with a pure `to_csv(report)` that uses the stdlib `csv` module and touches no database or clock.
  - It prefixes cells starting with `=`, `+`, `-` or `@` so spreadsheets don't run them as formulas.
  - A new `report_export` view sits next to `report_detail` in `views.py`.
  - Changing a CSV column then touches 1 file.
- **Move 2 – history (after Move 1):**
  - A new `app/reports/exports.py` with `record_export(...)` and `recent_exports(user_id, limit=5)`, backed by a new `report_exports` table with a copy of the title taken at export time.
  - The view passes the timestamp in, so tests don't need a clock.
  - A row is written only after the CSV builds successfully.
  - `report_list` shows the last 5.
  - Changing what the history shows touches 2 files.
- **Not built:** an exporter interface or format registry, since there is only one format today.

**Things to know first**
1. **Security gap:** `get_report(report_id)` (`models.py:10`) checks no owner. An export built on it would let any user download any report by guessing ids. Move 1 uses an owner-scoped lookup, but I did not change the existing `report_detail`, which has the same hole.
2. **One question:** is the button per report, or does it export the whole list? I designed for per-report, since your history records "the report title". A list export would change the CSV builder and the view but not the history table.
3. **Unspecified:** the repo has no schema or migration mechanism, so I don't know where the `report_exports` table gets created. The table is new, empty and read by nothing else, so I marked it two-way (drop the table to undo). Tell me if you want it treated as a one-way door.

<!-- file written by the agent: fixture/docs/arch-design.md -->
# ARCH-DESIGN
- at: no-git (fixture has no repository; analysis true of the 4 files under app/ as read 2026-09-30)
- question: where do a "download as CSV" button and a last-few-exports history live, so the next change to either lands in one place?
- yardstick: add or rename a CSV column (0 modules today, 1 after Move 1); change what the history shows or how many rows (0 today, 2 after Move 2: exports.py + views.py); add a second export format (0 today, 1 new module + 1 view after Move 1). Source: the request and its "for launch" wording; no git history or tracker exists to check.
- status: open
- verdict: clean
- context: the four files under fixture/app are the whole system; SQLite via app/db.py stays the only data access; views return plain data through render() and no HTTP framework is assumed; the button is per report (see Decision 1).

## Finding 1: report_detail reads a report by id with no owner check
- where: app/reports/models.py:10
- cost: 1 lookup by id only (views.py:10-11 passes no user); an export built on it would let any user download any report by guessing ids
- badge: strong
- evidence: traced, read models.py and views.py end to end; the only callers of get_report are views.py:10 (grep)

## Decision 1: what one export contains
- options: one report per click (title, created_at, body) | the whole reports list (id, title, created_at)
- forces: history records "the report title", which fits one report per export; a list export has no single title
- door: two-way, only the CSV builder and the view change
- evidence: suspected, the request is ambiguous; asked in the answer

## Decision 2: where history lives
- options: new table report_exports(id, user_id, report_id, report_title, exported_at) with the title copied at export time | no table, derive from a log
- forces: needs to survive restarts and be per user; a copied title stays true if the report is renamed or deleted; the table is new, empty, and read by nothing else, so dropping it is the rollback
- door: two-way, new table only, nothing existing altered
- evidence: traced, app/db.py:11 is the only write path and has no schema or migration mechanism in the repo

## Move 1: Pure CSV builder plus an owner-scoped export view
- cost: 0 files today; without this split the CSV logic ends up inside views.py, which already forwards to render() (views.py:14)
- pays: add or rename a CSV column: 1 file; add a second format: 1 new module
- files: app/reports/views.py:9, app/reports/models.py:10
- owner: new file app/reports/csv_export.py with to_csv(report) -> str, stdlib csv only, no db, no clock; it also prefixes cells starting with = + - @ with a single quote so spreadsheets do not run them as formulas
- callers: new report_export in views.py, placed next to report_detail, only; a new owner-scoped get is added in models.py; get_report at views.py:10 is left alone (Finding 1 is reported, not fixed here)
- door: two-way, land it and go
- proof: pytest tests/test_csv_export.py passes with a fixed report giving exact CSV text, a title containing a comma and a quote, and a cell starting with "="; a view test shows user B asking for user A's report gets not-found
- effort: S
- after: nothing

## Move 2: Export history behind two functions, written after a successful build
- cost: 0 files today; history done inline spreads a table, a query and a display format over the view
- pays: change history length or shown fields: 2 files (exports.py, views.py)
- files: app/db.py:11, app/reports/views.py:4
- owner: new file app/reports/exports.py with record_export and recent_exports (user_id, limit=5); it owns the table and its SQL; the view passes the timestamp in (UTC ISO string) so recording can be tested without a clock; recent_exports orders by id DESC with LIMIT and prunes nothing at launch
- callers: views.py only: report_export calls record_export after to_csv succeeds, report_list attaches recent_exports; db.py execute is reused as is
- door: two-way, new table only, rollback is dropping report_exports
- proof: pytest tests/test_exports.py against a temp sqlite file: 7 exports give the newest 5 in order; a second user sees none of them; a failed to_csv writes no row
- effort: S
- after: Move 1
