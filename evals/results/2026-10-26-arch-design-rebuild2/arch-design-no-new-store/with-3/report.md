# How to structure CSV export and export history in `fixture/`

**Verdict: the structure is clean, and the feature fits inside `app/reports/` with no new pieces.** There's one thing to fix first: anyone can currently open any report. A CSV download built on today's code would let anyone download any report.

The repo has no architecture doc or ADRs. Nothing in the repo was changed; I ran all checks in throwaway copies.

## What I found

1. **Any user can read any report (fix this first).** `get_report` (`app/reports/models.py:10-12`) looks reports up by id only, without checking the owner. `report_detail` (`app/reports/views.py:9`) passes the id straight through. I ran it in a temp copy: user 8 asked for report 1, which belongs to user 7, and got back `(1, 'Q3 sales', '2026-10-01', 'secret')`. If the CSV export reuses `get_report` as it is, it turns this into a one-click bulk download of anyone's reports.
2. **The repo doesn't define any tables yet.** It has no `CREATE TABLE` and no migrations folder; the schema lives somewhere outside the repo. Export history will be the first table the repo has to create itself, so someone has to decide where that definition lives.

## Recommended approach

Build the export and the history inside `app/reports/`, using the existing `db.execute`.

1. **Fix the leak.** Give `get_report` an `owner_id` argument and add `AND owner_id = ?` to its query. `report_detail` passes `request.user_id`. Owners see no difference.
2. **Add a `report_exports` table** to the existing SQLite database: `id, owner_id, report_id, title, exported_at`, indexed on `(owner_id, exported_at)`. Put the table definition in a schema file next to the models.
3. **Add two functions to `app/reports/models.py`:** `record_export(owner_id, report)` and `recent_exports(owner_id, limit=5)`, both going through `app.db.execute`.
4. **Add a `report_export_csv(request, report_id)` view in `app/reports/views.py`.** It fetches the report (now checked against the owner), writes it with Python's built-in `csv` module and records the export. It returns the file as a download (`Content-Disposition: attachment`). Escape any cell that starts with `= + - @` so a spreadsheet won't run it as a formula.
5. **Have `report_list` also return `recent_exports(request.user_id)`** so the reports page can show the history.

**Code that's affected:** `app/reports/views.py:1`, `:5` and `:10`. The users module only calls `execute` and doesn't change.

**What it reuses:** `app/db.py:11` (`execute`) already handles every connection and query. Export history goes in the same SQLite database rather than a second store, such as a log file, Redis or a separate exports database. A second store would mean another connection path, another thing to back up and secure, and a migration later to merge it back.

**Not doing:** saving CSV files to disk or cloud storage and building history from those files, or adding a background export queue. That brings file cleanup, access control on download links and a storage bucket to run, all for a launch that only needs a timestamp and a title. If exports later get big enough to need background jobs, they can go behind `report_export_csv` without changing the history table.

## Decision on where history is stored (hard to undo)

The history table is stored data, so this choice is hard to reverse later. What matters, most important first:

1. History belongs to the user and survives logging out or switching devices.
2. No new datastore to secure or back up.
3. History stays correct when a report is renamed or deleted.
4. As little code as possible at launch.

**Options:**
- **A:** A table on the server that stores a copy of the title and the export time for each export.
- **B:** The browser keeps the last few exports in local storage.

**I'd go with A** because of point 1: B loses the history on another browser or when storage is cleared, and the server never knows an export happened. Because A stores a copy of the title rather than looking it up from the report, it also meets point 3.

## Checking that behaviour doesn't change

The repo has no tests yet. This command, run from `fixture/`, sets up a temporary database and checks what `report_list` and `report_detail` return. It passes today; rerun it after each step:

```
python -B -c 'import os,sys,tempfile,types; sys.path.insert(0,"."); import app.db as db; db.DB_PATH=os.path.join(tempfile.mkdtemp(),"t.db"); db.execute("CREATE TABLE reports (id INTEGER PRIMARY KEY, owner_id INT, title TEXT, created_at TEXT, body TEXT)"); db.execute("INSERT INTO reports VALUES (1,7,\"Q3 sales\",\"2026-10-01\",\"a,b\")"); from app.reports.views import report_list, report_detail; r=types.SimpleNamespace(user_id=7); assert report_list(r)==[(1,"Q3 sales","2026-10-01")]; assert report_detail(r,1)[1]=="Q3 sales"; print("PROOF OK")'
```

After step 1, add a check that user 8 gets `None` for report 1.

## Also seen while reading
- **The leak above** is the serious one. It affects the existing detail page today, not just the new export.
- **`render`** (`app/reports/views.py:14`) just returns its input unchanged, so nothing renders a page or sets response headers yet. Whoever builds step 4 needs to decide how the CSV download response gets sent.

**Decision for you:** do you want to explore this approach as written, or first settle where the table definitions should live (finding 2)? Once it lands, I'd add a short `docs/architecture.md` and an ADR recording the server-side history decision.