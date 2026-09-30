**Verdict: the structure is clean, so add this inside `reports/` and don't restructure anything.** I chose "design new" for the feature. I read all four files in `fixture/`, about 45 lines in total (*traced*).

## One question first

Does "download as CSV on the reports page" export **the list** of reports (`report_list`) or **one report** (`report_detail`)? The history entry, "the report title", implies one report per export, so I've assumed a single report. If it's the list, the history row has no single title and product needs to say what to show.

## Structure

Each piece has one job, and the dependencies stay one-way (views → models → `db`).

| Piece | Responsibility | Must never know |
|---|---|---|
| `reports/csv_export.py`, new | `to_csv(report) -> str`. It's a pure function that uses stdlib `csv` and formula-escapes cells that start with `= + - @`. | the DB, the request |
| `reports/models.py:` add `record_export(owner_id, report_id, title)` and `recent_exports(owner_id, limit=5)` | It owns the history table, through `app.db.execute` (`db.py:11`). | CSV, HTTP |
| `reports/views.py:` add `report_export(request, report_id)`. Extend `report_list` (`views.py:4-6`) to include `recent_exports`. | It checks ownership, calls `get_report` and `to_csv`, then calls `record_export` and returns the download response. | SQL, CSV rules |

- **History table:** `export_history(id, owner_id, report_id, title, exported_at)`. It sits in the same SQLite database, and there is no new store or dependency.
- **Errors:** an unknown or foreign report returns the same not-found response. If `record_export` fails, log it and still serve the file. A missing history row is a smaller failure than a blocked download.

## Two options for the history store

- **A. Table in the existing DB (recommended).** `app/db.py` already owns all persistence (`db.py:1`). The history survives sessions and devices, and it's a few lines in `models.py`.
- **B. Session or cookie.** It needs no schema, but history disappears on logout or a new device. It only meets the requirement if "last few" means "this session".

**Door:** the table shape is one-way once it holds real data. Two decisions go with it:
- **Title:** I'd store a snapshot of the title, so history stays readable after a rename or delete. The alternative is joining on `report_id`, which shows the current title but breaks on deleted reports.
- **Schema:** I found no DDL or migrations in `fixture/`, so I can't say how `reports` is created (*suspected*: it lives outside this tree). The new table has to follow that mechanism.

## Things to handle in the design

1. **Ownership check, required.** `get_report` (`models.py:10-14`) filters by `id` only, and `report_detail` (`views.py:9-11`) passes no owner. The export must not copy this. Any user could otherwise download any report by guessing ids. Add an `owner_id` filter, either as an optional argument or a sibling function. The existing hole in `report_detail` is a separate issue that I'm flagging and not fixing.
2. **CSV formula injection.** Titles and bodies are user-controlled, so the escaping in `to_csv` is part of the design.
3. **No response layer here.** `render` (`views.py:14-15`) just returns data. The download needs `Content-Type` and `Content-Disposition` headers, and the framework isn't in `fixture/`. Keep the header code in `report_export`.

## Pre-mortem

- **History fills up with junk or grows forever:** `LIMIT 5` on read is enough for launch. Prune on insert only if the table grows.
- **Large reports blow memory or time out:** the body is loaded whole (`models.py:11`). Accept this for launch and cap the size. Streaming or async export is speculative, so I'm not designing it.
- **Someone asks for XLSX or JSON next:** don't add a format seam for one format. A second format is when `csv_export.py` earns a sibling.

## Moves and proof

Each move lands on its own, with behavior unchanged elsewhere.
1. **`to_csv` plus tests.** The check is that `to_csv` escapes `=cmd`, quotes commas and newlines, and round-trips through `csv.reader`.
2. **`export_history` table plus `record_export` and `recent_exports`.** The check is that 7 exports return the latest 5, newest first, scoped per owner.
3. **`report_export` view with the ownership check.** The check is that owner A gets the CSV and the history row is written. Owner B requesting A's report gets not-found and no row.
4. **Show `recent_exports` in `report_list`, then add the button.**

Total: about 3 files touched and 1 added. I ran nothing; there are no tests or git history in `fixture/` to run.

Answer the single-report versus list question and the title-snapshot choice, and this is ready for `plan-work`.