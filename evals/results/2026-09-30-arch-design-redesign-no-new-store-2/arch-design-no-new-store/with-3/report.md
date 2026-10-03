**Recommendation: keep the CSV button and the history inside `app/reports/`, and store history as one new table through the existing `app/db.py`. Don't add a new package, a plugin seam or a dependency.**

I read all four files in `fixture/` (*traced*). There is no git history and no template layer, so I didn't run the change-history or import-graph scripts. The fixture has no imports to speak of beyond `app.db`. I wrote no `docs/arch-design.md`. The design is small enough to answer here, and I can write the file if you want it.

## Structure

| Piece | Where | Notes |
|---|---|---|
| CSV formatting | new pure function `reports_to_csv(rows) -> str` in `app/reports/csv_export.py` | Stdlib `csv` only, no I/O. It also neutralises cells starting with `=`, `+`, `-` or `@` (spreadsheet formula injection). |
| History storage | `record_export(...)` and `list_recent_exports(user_id, limit=10)` in `app/reports/models.py` | Same style as `list_reports` at `models.py:4`, going through `db.execute` (`db.py:11`). |
| Export endpoint | `report_export(request, report_id)` in `app/reports/views.py` | It fetches the report, builds the CSV, records the export, then returns the CSV. |
| History display | `report_list` (`views.py:4`) also returns `list_recent_exports` | It shows a timestamp and title. |

- **Other options:** I considered a separate `app/exports/` package. It has the same reasons to change as reports, and it would be a second owner for a small job. I also considered keeping history in the session or a cookie. That is simpler, but it doesn't survive across devices or sessions, and "last few exports" implies it should. Confirm that with Product.
- **The table:** `report_exports(id, owner_id, report_id, title, exported_at)`.
  - Store the title as a snapshot rather than joining to `reports`. A report can be renamed or deleted, and the history should still read correctly.
  - Store `exported_at` in UTC and pass it in from the view. That way `record_export` can be tested without the clock.
  - Trim by `ORDER BY exported_at DESC LIMIT 10` on read. Don't prune on write for launch.
- **Recording:** record the export only after the CSV was built successfully, so a failed export leaves no history row.

## Things to fix in the design before anyone builds

1. **Ownership check (*traced*).** `get_report(report_id)` at `models.py:10-14` doesn't filter by owner. `report_detail` (`views.py:9-11`) has the same gap. If the export view reuses it as-is, any user can export any report by guessing an id. The export must fetch the report scoped to `request.user_id`, for example a new `owner_id = ?` variant. I'm flagging the existing detail-view gap but not proposing to fix it here.
2. **Formula injection.** Report titles and bodies are user text. Without escaping, a title like `=HYPERLINK(...)` runs when someone opens the CSV in Excel.
3. **The button.** `render` is a passthrough stub (`views.py:14-15`) and `fixture/` has no templates, so I can't say where the button goes. That belongs to whatever renders the reports page.

## Parked, needs a yes

**The `report_exports` table is a one-way door** because it is stored data shape. Confirm these before any migration is written:
- the column set above;
- whether history is per user (I assumed so);
- whether the title snapshot is what Product wants.

I also can't see how tables are created. There is no schema or migration file in `fixture/`, so I can't say where the `CREATE TABLE` belongs.

**Question for Product:** which columns go in the CSV? Just `id, title, created_at`, or also `body`? Body can be large, and that changes whether the export should stream.

## Landing order

1. `reports_to_csv` plus its tests, including the formula-injection cases. Two-way door.
2. The owner-scoped report fetch. Two-way door.
3. The `report_exports` table, `record_export` and `list_recent_exports`. Needs the yes above.
4. The `report_export` view and the history on the list page.

Each one lands alone. The check for the whole feature is: export a report as user A and get the CSV plus one history row; export the same id as user B and get nothing and no row.