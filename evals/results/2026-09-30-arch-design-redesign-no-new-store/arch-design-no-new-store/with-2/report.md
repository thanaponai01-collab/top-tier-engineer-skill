The design is written up and `arch-design.py check` exits 0. The plan is four small pieces in `fixture/app/reports/`, plus one security gap in the existing code that the export must not copy. This is a design only, so no code was written.

**Structure**
- **Serializer:** a new `csv_export.py` holds a pure function that turns one report row into CSV text. It uses the stdlib `csv` module for quoting and neutralises cells starting with `=`, `+`, `-` or `@`, so a report title or body can't inject a spreadsheet formula. It never touches the database or the clock.
- **History:** a new `exports.py` records and reads exports through `app.db.execute`. It stores a user id, a report id, a title snapshot and a timestamp. It reads the last 5 per user, newest first, and the caller passes in the timestamp.
- **Views:** `views.py` gets `report_export` (a POST that returns the CSV and then records the history row) and a separate `export_history` view. Nothing is recorded if building the CSV fails.
- **Ownership:** a new `get_owned_report(report_id, owner_id)` in `models.py` is what the export uses to load the report.
- **Existing gap:** `get_report` at `models.py:10` has no owner filter, so an export built on it would let any user download any report by guessing its id. I left `report_detail` alone. Whether it should also be scoped is your call.

**Decisions**
- **Storage:** history goes in a database table rather than the session, so it survives logout. The table is additive and only this feature reads it, so it is easy to drop or change. It becomes harder to change once launch data accumulates.
- **Title snapshot:** the history row stores the title as it was at export time, not a join to the report. It survives renames and deletes.
- **POST, not GET:** a GET that writes history would fire on prefetch and link scanners. History also gets its own endpoint, because `report_list` returns a bare list and its consumers sit outside `fixture/`.

**Questions for you**
1. **One report or the whole list?** I assumed one report per click. Exporting the whole list would make "report title" in the history meaningless.
2. **Where is the schema?** No file in `fixture/` creates the `reports` table, so I don't know where the new history table's DDL should go.
3. **What should the CSV contain?** `body` is a single text blob, so a one-report export is one row of id, title, created_at and body. Confirm that is what product wants.

**Limits**
- `fixture/` is a 4-file Python fragment with no git history, no tests and no template layer.
- I ran no import-graph or change-history tooling, so the yardstick is assumed from your request and the rehearsal is what I traced by reading the files.
- The button itself lives outside `fixture/` and isn't designed here.

The full design, including the four moves in landing order, is in `docs/arch-design-csv-export.md`.

<!-- file written by the agent: docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: no-git (not a repository; analysis true of the 4 files under fixture/app on 2026-09-30)
- question: where do a CSV export and a per-user export history go in fixture/, before anyone writes code?
- yardstick: add or rename a CSV column (0 modules today, no export exists; target 1); change how many past exports are shown (target 1); export a second thing such as users (target 1 new serializer, 0 edits to history). Source: the user's request only, with no git history or tracker to read, so the second and third are assumed.
- status: open
- verdict: clean
- context: the app stays a plain-function layout (views -> models -> app.db.execute); no ORM, no framework is introduced; the template/UI layer is outside fixture/ and is not designed here.
- assumption: "download as CSV" means one report per click (a button per row on the report list, or on the detail page). Exporting the whole list would make "report title" in the history meaningless. Asked below.

## Finding 1: report_detail reads a report by id with no owner check
- where: fixture/app/reports/models.py:10
- cost: 1 of 2 report read queries filters by owner (list_reports at models.py:6 does; get_report at models.py:12 does not). An export built the same way as get_report would let any user download any user's report body by guessing an id.
- badge: strong
- evidence: traced, read models.py and views.py end to end; no other caller of get_report exists in fixture/ (grep-level, and callers outside fixture/ are not visible).

## Finding 2: nothing in fixture/ defines the reports table
- where: fixture/app/db.py:1
- cost: 0 schema files or migrations among 4 files; the history table has no evident home. Where DDL lives is unknown.
- badge: worth exploring
- evidence: traced, Glob of fixture/ returned 4 files, none containing CREATE TABLE.

## Decision 1: where export history is stored
- options: A) a `report_exports` table via app.db.execute (user_id, report_id, report_title, exported_at) | B) session or client-side storage
- forces: "last few exports a user ran" implies it survives across sessions and devices (pushes A); B needs no schema but loses history on logout. app.db is already the single data-access path (db.py:1).
- door: two-way. The table is additive, read only by this feature, and holds convenience data, so dropping it loses only history. It stops being cheap to change once launch data accumulates; revisit if history becomes an audit record.
- evidence: traced, from db.py and models.py.

## Decision 2: the history row stores a title snapshot, not just the report id
- options: A) store report_title at export time | B) store report_id and join to reports for the title
- forces: A survives rename or delete of the report and needs no join; B avoids duplicated data. The request is "timestamp and report title", and a title as it was at export time is the literal reading.
- door: two-way (one column, same table as Decision 1)
- evidence: traced.

## Decision 3: export is a POST, and the history is its own endpoint
- options: A) POST /reports/<id>/export returns the CSV and records the history row; separate GET for history | B) GET download that logs as a side effect, with history folded into report_list's return value
- forces: a GET that writes gets triggered by prefetch, link scanners and retries; report_list returns a bare list (views.py:6), and adding history to it changes a shape whose consumers are outside fixture/ and not visible.
- door: two-way (internal routes, no external consumers visible)
- evidence: traced for the view shapes; the external template's use of report_list is suspected.

## Move 1: add an owner-scoped report fetch for export
- cost: 1 of 2 report read queries has no owner filter (models.py:12); export would inherit the gap.
- pays: export a report: cannot leak another user's body. Every later export (a second entity, a bulk export) reuses the same ownership rule.
- files: fixture/app/reports/models.py:10-14
- owner: reports/models.py, one function `get_owned_report(report_id, owner_id)` selecting id, title, created_at, body WHERE id = ? AND owner_id = ?
- callers: the new export view only. report_detail (views.py:11) keeps calling get_report unchanged; whether it should also be scoped is an existing bug raised separately, not fixed here.
- door: two-way, land it and go
- proof: a test that a second user's id gets None for the first user's report, and the owner gets the row. New test; replaces no old tests (none exist in fixture/).
- effort: S
- after: nothing

## Move 2: add a pure CSV serializer for a report row
- cost: 0 today; without it, quoting and column order end up inline in the view.
- pays: add or rename a CSV column: 1 file (csv_export.py). Formula-injection escaping has one owner.
- files: fixture/app/reports/models.py
- owner: new file fixture/app/reports/csv_export.py (models.py is only the neighbour it sits beside, unchanged), `to_csv(report_row) -> str`. Uses stdlib `csv` for quoting, fixed header (id, title, created_at, body), and prefixes cells that begin with = + - @ with a single quote. It takes a row and returns text, with no db, no clock and no request.
- callers: the export view (Move 4)
- door: two-way, land it and go
- proof: unit tests with no database: a title containing comma, quote and newline round-trips through csv.reader; a body of `=cmd|' /C calc'!A0` comes out neutralised; header order is fixed.
- effort: S
- after: nothing

## Move 3: add export history storage and read
- cost: 0 today; no home for the table (Finding 2).
- pays: change how many exports are shown: 1 constant; export a second entity: 0 edits, since history is keyed on title and id.
- files: fixture/app/db.py
- owner: new file fixture/app/reports/exports.py (the DDL goes wherever the reports table is created, which is unknown, see Finding 2), `record_export(user_id, report_id, report_title, exported_at)` and `recent_exports(user_id, limit=RECENT_LIMIT)` returning newest first, `RECENT_LIMIT = 5`. The caller passes `exported_at`, so the module never reads the clock. Both go through app.db.execute.
- callers: the export view and history view (Move 4)
- door: two-way, per Decision 1
- proof: with a temp sqlite file set as db.DB_PATH: record 7 exports for user 1 and 1 for user 2; `recent_exports(1)` returns 5 rows, newest first, and none belong to user 2.
- effort: S
- after: nothing

## Move 4: wire the two views and the button
- cost: 0 today.
- pays: the button and the history become reachable; the view stays thin, at fetch, serialize, record, return.
- files: fixture/app/reports/views.py
- owner: views.py gains `report_export(request, report_id)` and `export_history(request)`; the button itself lives in the template layer outside fixture/. views.py holds routes only; ownership stays in models (Move 1), format in csv_export (Move 2), history in exports (Move 3).
- callers: whatever routing and template code sits outside fixture/ (not visible); the button posts to report_export
- door: two-way, land it and go
- proof: view-level tests. Owner POSTs, gets CSV text plus one history row. A non-owner POST gets not-found and writes no history row. A failed serialization writes no history row (record only after the CSV is built). `export_history` returns only the caller's rows.
- effort: M
- after: Move 1, Move 2, Move 3
