The structure is fine for this feature: build CSV export and export history inside the existing `reports` module, with no new package. But first, any user can currently read any other user's report. The export must not be built on top of that.

## Fix this first: reports have no owner check
`get_report` (`app/reports/models.py:10`) looks a report up by id only. `report_detail` (`app/reports/views.py:9`) calls it without checking who is asking. I ran it in a throwaway copy: user 8 opened user 7's report and got the full body back. A CSV export that reuses `get_report` would hand out the same data as a downloadable file.

## Recommended structure
Everything goes in `app/reports/`, and every query goes through the existing `app/db.py:11` `execute`.

1. **`get_owned_report(report_id, owner_id)`** in `models.py`, filtering on `WHERE id = ? AND owner_id = ?` the same way `list_reports` (`models.py:4`) already does. Leave `get_report` as it is for now so nothing that works today changes yet.
2. **`export_csv(report)`**, using Python's built-in `csv` module so commas and quotes in the report body come out correctly.
3. **A new `report_exports` table** with `id, owner_id, report_id, title, exported_at`, plus `record_export(...)` and `recent_exports(owner_id, limit=5)`.
4. **A `report_export_csv` view**, which looks up the owned report (returns 404 if it isn't theirs), builds the CSV, records the export, and returns the file as a download.
5. **An `export_history` view**, which returns `recent_exports(request.user_id)`.
6. **As its own ticket:** switch `report_detail` to `get_owned_report`. That closes the existing hole, but it changes current behaviour, so it should be reviewed on its own.

The only file that imports `app.reports.models` is `app/reports/views.py:1`. `app/users/models.py` uses `execute` but isn't affected.

## The one decision that's hard to undo: what the history table stores
Once export rows are being saved, changing their shape later is costly, so I ranked what matters first:
1. The history should still read correctly after a report is renamed or deleted.
2. A user should only see their own exports.
3. No new infrastructure beyond the existing sqlite database.

- **A (recommended):** each history row saves a copy of the report title as it was at export time.
- **B:** each row saves only the report's id and looks up the title when the history is shown.

I recommend A because of point 1. With B, a renamed report would show its new title in the history, and a deleted report's row would come up blank or disappear. Neither matches what "the export I ran" means.

**What I'm not recommending:** a separate `exports/` module or a general audit-log service. Either would split one small feature across two packages and duplicate the report lookup, including its owner check. If history ever needs to become a site-wide audit log, moving it later means moving one table and rewriting `recent_exports`.

## Other things to know before building
- The repo has no table definitions or migrations, and `DB_PATH` is a relative path (`app.sqlite3`). Decide where the `CREATE TABLE report_exports` statement will live before building.
- `render()` just returns the data it's given, and there's no response object. The download needs somewhere to set the CSV content type and the `Content-Disposition` header, which tells the browser to save the file. Nothing in the repo does that today.

## Check that nothing breaks
This passes today from `fixture/` (run in a throwaway copy). Rerun it after each step:
```
python -B -c "import os,tempfile; import app.db as d; d.DB_PATH=os.path.join(tempfile.mkdtemp(),'t.db'); d.execute('CREATE TABLE reports(id,title,created_at,body,owner_id)'); d.execute(\"INSERT INTO reports VALUES(1,'Q3','2026-01-01','a,b',7)\"); from app.reports.models import list_reports,get_report; from app.reports import views; assert list_reports(7)==[(1,'Q3','2026-01-01')]; assert get_report(1)[1]=='Q3'; print('ok')"
```

I didn't change anything in the repo, and the arch-design helper's final check passed. Do you want to go ahead with this design, history option A included, or explore something else first, such as fixing the owner check before the export work starts?