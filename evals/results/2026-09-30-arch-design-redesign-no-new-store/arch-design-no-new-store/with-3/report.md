**Verdict: the code is clean, so no restructuring is needed. Add the feature as two small pieces inside `app/reports/`. One decision needs your yes before the history part can be designed further.**

The design is in `docs/arch-design-csv-export.md` and its check passes. There is no git history and no import-graph tooling for four files, so everything here comes from reading all four files (*traced*).

**Structure**
- **CSV export:** put the row-to-CSV logic in a new `reports/export.py`. It uses stdlib `csv` and no new dependency. `views.py` only wires the request to it and sets the download headers. Adding a column then touches one file.
- **Data source:** the export reuses `list_reports` (`models.py:4-7`), which is already scoped by owner.
- **History:** put reading and writing history in a separate `reports/history.py`, with `record_export(user_id, report_id)` and `recent_exports(user_id, limit)`.
  - The export view calls `record_export`.
  - The report list view calls `recent_exports`.
  - Storage is a new `report_exports` table written through `app/db.py:11`.
- **Sync:** generate the CSV inside the request. There is nothing in the repo suggesting reports are big enough to need a stored file.

**Existing risk**
- **What:** `get_report` (`models.py:10`) filters by id only, with no owner check. `list_reports` does filter by owner.
- **Impact:** if the export path copied the detail path, any user could export any report and write it to history.
- **Fix:** scope the query by owner first (Move 1 in the file). If an upstream layer already enforces ownership, that layer is outside this repo and I couldn't see it.

**Needs your yes (parked, left out of the file):** where history is stored. This is a one-way door because it fixes the shape of stored data.
- **Recommended:** a new table with `report_id` and `exported_at`, showing the last 10 by `LIMIT`. Join to `reports` for the title, and show "(deleted)" if the report is gone.
- **Alternatives:**
  - Copy the title into the history row. It survives deletion but goes stale after a rename.
  - Keep history in the session. It's lost on restart and not shared across devices.
- **Cost of being wrong:** a table is the hard one to undo once users have history in it.

**Unknowns**
- **Table creation:** no schema or migration files exist in the repo, so I don't know where tables are created. Find that before building the history move.
- **Routing:** the routing file isn't in the repo either, so I couldn't say where the button's route goes.

The file has two moves in order: owner scope on `get_report`, then the export view with `export.py`. The history move is left out until you confirm the storage choice.

<!-- file written by the agent: docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: no git repo (4 files read in full, 2026-09-30)
- question: where do "download reports as CSV" and a short export history live in fixture/app?
- yardstick: add a column to the export (touches 1 module: reports/models.py:5-7 + new export code); change how many history rows show (1 module); add a second exportable thing, e.g. users (0 today, would be 1 new module)
- status: open
- verdict: clean
- parked: export history storage (new table vs. session, join vs. copied title) is a one-way door awaiting a yes; history move is left out until then
- context: sqlite via app/db.py:11 `execute` stays the only DB access; `reports` is the only domain module involved; auth is `request.user_id` (reports/views.py:5); no schema/migration files exist in the repo, so table creation is owned elsewhere (unverified)

## Finding 1: report_detail has no owner check
- where: fixture/app/reports/models.py:10
- cost: get_report(report_id) filters by id only; list_reports (models.py:6) filters by owner_id. An export endpoint copying the detail path would let any user export any report and write it to history. 1 call site today (views.py:11).
- badge: worth exploring
- evidence: traced, read models.py and views.py end to end. Whether an upstream layer enforces ownership is not visible in the repo.

## Decision 1: where export logic lives
- options: new `app/reports/export.py` (CSV building) + `app/reports/history.py` (history read/write), called from views.py | put everything in views.py/models.py
- forces: views.py is 16 lines and is HTTP-shaped; CSV formatting and history are separate reasons to change (column set vs. retention/display). Two files under reports/ keep the package the single owner of "reports".
- door: two-way
- evidence: traced, file layout and imports read this session

## Decision 2: sync vs. stored file
- options: generate CSV in the request and stream it back (stdlib `csv`, no new dependency) | generate async and store a file
- forces: reports are read via one `SELECT ... WHERE owner_id = ?` (models.py:5-7), no size signal in the repo. Simplest option meets "download button".
- door: two-way
- evidence: suspected on size; revisit if a user's report count is large

## Move 1: scope get_report by owner (only if no upstream check exists)
- cost: 1 unscoped query, models.py:10-14
- pays: makes the export path safe to add, 1 function changed
- files: fixture/app/reports/models.py:10, fixture/app/reports/views.py:11
- owner: reports/models.py
- callers: report_detail (views.py:9-11)
- door: two-way, land it and go
- proof: test that user B calling get_report(id_of_A_report, B) gets None; existing detail call for owner still returns the row
- effort: S
- after: nothing

## Move 2: add reports/export.py and export view
- cost: 0 today; without this, CSV logic lands in views.py
- pays: add a column to the export: 1 file
- files: fixture/app/reports/views.py:1-16 (add the view beside report_list; export.py is created here)
- owner: export.py owns row-to-CSV; views.py only wires request to it and sets download headers
- callers: new route for the button (routing file is not in the repo; find it before building)
- door: two-way, land it and go
- proof: test feeding list_reports rows and asserting exact CSV text, including a title with a comma and a quote
- effort: S
- after: Move 1
