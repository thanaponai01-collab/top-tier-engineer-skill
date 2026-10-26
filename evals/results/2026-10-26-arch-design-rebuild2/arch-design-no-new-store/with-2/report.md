I ran arch-design in design mode over `fixture/` and all three stages pass (`ARCH-GATE: done`). I didn't change anything in the repo; the check scripts ran in a throwaway copy. My recommendation: keep both features inside `app/reports/`, store the export history as one new table in the existing SQLite database, and fix one access-control gap before the export goes in.

**Verdict: the code is clean.** It's small, well layered and easy to extend. All queries already go through `app/db.py::execute`, and the reports query code already lives in `app/reports/models.py`. The one real risk is that **report detail doesn't check who owns the report**, and an export built on top of it would expose data the same way.

There's no `docs/architecture.md` or ADR folder in the repo, so there was no existing design doc to check against.

## Finding: report detail returns any report to any user
- **Where:** `app/reports/models.py:10` and `app/reports/views.py:9`
- **Evidence:** traced through the code. `report_detail` calls `get_report(report_id)`, whose SQL filters on `id` only. Nothing compares `owner_id` to `request.user_id`.
- **Cost:** there is one unprotected read path today. If the CSV button reuses `get_report`, there are two endpoints that give any report's body to any logged-in user, and two places to fix later.

## The move: CSV export and export history in `app/reports`, limited to the report's owner
**What changes (all new code; nothing existing is removed or renamed):**
- `get_report_for_owner`, `record_export` and `recent_exports` in `app/reports/models.py`
- a `report_export_csv` view in `app/reports/views.py`
- a new `report_exports` table: `id, user_id, report_id, report_title, exported_at`

**Steps (each one leaves current behaviour unchanged):**
1. Add `get_report_for_owner(report_id, owner_id)`, which filters on `id = ? AND owner_id = ?`. Leave `get_report` as it is for now.
2. Create `report_exports` with `CREATE TABLE IF NOT EXISTS`. The repo has no schema or migration files at all, so this is effectively the first one; decide where it lives.
3. Add `record_export(user_id, report_id, title)` and `recent_exports(user_id, limit=5)`, both going through `app.db.execute`.
4. Add `report_export_csv(request, report_id)`:
   - call `get_report_for_owner` and return a 404 if it comes back empty;
   - build the CSV with Python's built-in `csv` module;
   - call `record_export`;
   - return it with `Content-Type: text/csv` and `Content-Disposition: attachment`.
5. Have `report_list` also return `recent_exports(request.user_id)` so the page can show the history panel.
6. As a separate change with its own review, switch `report_detail` to `get_report_for_owner`. That closes the existing gap.

**Who's affected:** only `app/reports/views.py:1` imports `app.reports.models`. `app/db.py::execute` is also used by `app/users/models.py:1`, which doesn't change.

**Proof:** this command, run from `fixture/`, passes today in a throwaway copy and exercises the existing report queries. Rerun it after each step and add asserts for the new functions as they land:
```
python -B -c "import tempfile,os,app.db as d; d.DB_PATH=os.path.join(tempfile.mkdtemp(),'t.db'); d.execute('CREATE TABLE reports(id INTEGER PRIMARY KEY, owner_id, title, created_at, body)'); d.execute(\"INSERT INTO reports VALUES(1,7,'Q3','2026-10-01','x')\"); from app.reports import models as m; assert m.list_reports(7)==[(1,'Q3','2026-10-01')]; assert m.get_report(1)[1]=='Q3'; print('ok')"
```

**What it reuses:** `app/db.py:11` (`execute`), which is already the one place that opens connections, and the reports query module in `app/reports/models.py`.

**What it avoids adding:** a second place to keep history (a JSON file, Redis, browser localStorage, or a separate database). Each would need its own connection code, backups and access control. localStorage would also lose the history when the user switches browser or device.

**Not doing:**
- **A general "exporter" plugin system** for future formats. With only CSV, it's an abstraction with one use, and every change would touch two extra files until a second format exists.
- **Generating the CSV in a background job.** That adds a queue to run and a "your file is ready" flow, for a report that's a single query.

If storing history in the database turns out to be wrong (for example, history must be shared across a team), the fix is a new column, not moving data out of a different store.

## Decision: where the export history is stored (stored data, so hard to undo)
**Criteria, in priority order:**
1. One owner for stored data and its access control.
2. History survives across devices and sessions for the same user.
3. Smallest change for launch, which only needs timestamp and title.

**Options:**
- **A:** the `report_exports` table in the existing SQLite database, with the report title copied at the moment of export.
- **B:** no table; keep the last few exports in the browser (localStorage) or in the session.

**Chosen: A, because of criteria 1 and 2.** B keeps history outside the server's access control and loses it on another browser. A costs one table and three small functions.

Copying the title at export time means the history shows what the user actually downloaded, even if the report is renamed later.

## Other problems I noticed
- **Missing owner check on report detail** (the finding above). This is a real security hole today, independent of the CSV work, and worth fixing even if the feature slips.
- **No schema in the repo.** Nothing creates the `reports` or `users` tables, so wherever that setup actually lives needs to own the new table too.
- **Relative database path.** `DB_PATH = "app.sqlite3"` resolves against whatever folder the app is started from, so starting it from a different folder silently creates a new, empty database.
- **`render` does nothing yet** (`views.py:14` just returns the data). The CSV view will need a real way to return headers and a file body.

Do you want to go with this move as described, or explore the alternative (history kept in the browser) or a different scope for step 6 first? Once it lands, I can add a `docs/architecture.md` and a short ADR recording the storage decision.