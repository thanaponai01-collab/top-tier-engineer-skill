**Verdict: `fixture/` is clean and small, so this fits in its existing structure with no new layers. The export-history table is parked until you confirm it.** I wrote `docs/arch-design.md` and its `check` exits 0. I read all four files (*traced*). The fixture isn't a git repo, so there was no change history to mine and the file's `at:` field just says so.

**Structure**
- **CSV builder:** a pure `to_csv(report) -> str` in a new module inside `app/reports/`, using stdlib `csv` and no db import. It is one function, not a format registry, because there is one format.
- **Export view:** `report_export` goes beside `report_detail` in `views.py`. It calls `get_report`, then `to_csv`.
- **History:** SQL goes in `app/reports/models.py`, next to `list_reports`, through `app.db.execute`. That is the one place that opens connections (`db.py:1`). It adds `record_export` and `recent_exports(owner_id, limit)`. This stays in the reports package and doesn't get its own module.

**Needs your yes: where history is stored**
- I recommend a `report_exports(id, report_id, owner_id, exported_at)` table in the existing sqlite DB. It survives restarts and adds no new store.
- It is a stored-data-shape change, which is hard to reverse. The fixture has no schema or migration file (*traced*), so I don't know how tables get created here.
- The alternative is an in-memory or per-session list. That is cheap but loses history on restart.
- I left the history move out of the file, as the skill requires for unconfirmed one-way doors.

**Finding: `get_report` takes only `report_id`, with no owner check** (`views.py:9`, `models.py:10`). `report_list` scopes by `request.user_id`, but `report_detail` doesn't. If export reuses `get_report` as-is, any user can download any report by id. Move 2 puts the owner check in the export view. I only read the fixture, so I can't rule out a check elsewhere in the real app.

**Moves in the file** (both two-way, effort S)
1. The pure CSV builder. Its test covers titles with a comma, a quote, a newline and a leading `=`. The leading `=` is the spreadsheet formula-injection case.
2. The export view with the owner check. Its test shows user A gets their own CSV and user B's report id is refused.

**One question that changes the work:** what does the CSV contain?
- I assumed one report's content, because the history stores "report title".
- If it means the whole report list (`id, title, created_at`), the builder takes `list_reports` rows and the owner-check finding mostly goes away.
- The fixture doesn't say what format `body` is in, so the per-report CSV columns are also unspecified.

**Not covered:** the route table isn't in the fixture, so wiring the button and URL belongs to whoever owns routing.

<!-- file written by the agent: docs/arch-design.md -->
# ARCH-DESIGN
- at: no-git (fixture/ is not a repository; STALE cannot be computed)
- question: where does "download as CSV" plus a short export history go in fixture/?
- yardstick: add a column to the CSV (0 modules exist yet, target 1); change how many exports history shows (target 1); add a second export format (target 1 new function); source: product request, no git history to mine
- status: open
- verdict: clean
- parked: export history storage (one-way: new table) and its move; see chat, needs a yes
- context: sqlite via app/db.py stays the only data access; reports stay owned by app/reports; no auth/session model exists in the fixture and none is added

## Finding 1: report_detail has no owner check, so an export built on get_report inherits it
- where: fixture/app/reports/views.py:9
- cost: 1 of 2 report views scopes by owner (report_list passes request.user_id, views.py:5); get_report (models.py:10) takes only report_id
- badge: worth exploring
- evidence: traced, read all four files; whether a caller elsewhere checks ownership is suspected (fixture has no other callers)

## Decision 1: CSV building
- options: one pure function in app/reports/export.py | a formatter registry with a CSV plugin
- forces: one format asked for; a seam with one implementer is a guess
- door: two-way
- evidence: traced

## Move 1: pure CSV builder
- cost: no CSV code exists; without one owner the first view to need it will inline it
- pays: add a CSV column: 1 file; add a second format later: 1 new function beside it
- files: fixture/app/reports/models.py:10 (row shape it reads); the builder is a new sibling module in the same package
- owner: a new export module in app/reports, `to_csv(report) -> str`, stdlib csv, no db import
- callers: the export view only
- door: two-way, land it and go
- proof: `pytest fixture` with a unit test on a literal row incl. a title containing a comma, a quote, a newline and a leading `=`; passes; nothing existing changes
- effort: S
- after: nothing

## Move 2: export view with owner check
- cost: see Finding 1
- pays: the button gets one entry point; ownership enforced in one place
- files: fixture/app/reports/views.py:9 (add `report_export` beside `report_detail`); fixture/app/reports/models.py:10 (owner_id needed in the row or a scoped getter)
- owner: views.report_export, calls get_report then to_csv
- callers: the route table (not in fixture; must be added by whoever owns routing)
- door: two-way, land it and go
- proof: test that user A gets 200 and CSV for own report and a refusal for user B's report id; existing `report_detail` behavior unchanged
- effort: S
- after: Move 1
