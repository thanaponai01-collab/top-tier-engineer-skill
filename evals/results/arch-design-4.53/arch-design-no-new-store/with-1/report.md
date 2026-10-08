**Verdict: clean.** The structure is small and sound, so I'm treating this as design-new inside the existing layout, not a restructure. I read all four files in `fixture/` (traced). There are no routes, templates, tests or schema files, so I couldn't check anything outside those four.

## How to structure it

**Reuse what exists.** `app/db.py:11` `execute()` is the one place that runs queries, and `app/reports/models.py` owns report reads. Put the new code beside them. Don't add a new layer, a service class or an exporter plugin interface. There is one format, so it's one function.

| Piece | Responsibility (and what it must not know) | Location |
|---|---|---|
| `to_csv(rows) -> str` | Turns report rows into CSV text. It's pure, so it never touches the DB, the request or the clock. | new `app/reports/export.py` |
| `record_export(user_id, report)` and `recent_exports(user_id, limit=5)` | Own the history table. They know nothing about CSV or HTTP. | new `app/reports/export_history.py`, using `execute()` |
| `report_export_csv(request, report_id)` | Fetches the report, builds the CSV, records the export, returns the download. | `app/reports/views.py` |
| Existing `report_list` | Also fetches `recent_exports` for the page's history panel. | `app/reports/views.py:4` |

Dependencies point one way: views → export and export_history → `db`. I'd keep history out of `reports/models.py` because the two change for different reasons (retention and UI, versus the report schema).

**Contracts.**
- **Order of operations:** build the CSV first, then record the export, then return the file. A failed generation leaves no history row.
- **Failures:** a missing report returns 404. A history-write failure should not block the download, so log it and continue.

## Decisions to settle before code

1. **What gets exported?** I need an answer to this one first. "Report title" in the history suggests one report per export. "Button on the reports page" could also mean the list (`list_reports`, `models.py:4`). I'd assume per-report (`id, title, created_at, body`) unless Product says otherwise. The history table below works either way if `report_id` is nullable for a list export.

2. **Where history lives (one-way door: a stored data shape).**
   - **A. Server table (recommended):** `export_history(id, user_id, report_id, report_title, exported_at)`.
     - Persists across devices.
     - Snapshot the title, so a later rename or delete doesn't rewrite history.
     - Store `exported_at` as UTC ISO text.
     - Keep the last N by query (`ORDER BY exported_at DESC LIMIT 5`) and skip pruning at launch.
   - **B. Browser localStorage:** no schema and no migration, but history is per-device and the server can't see it.
   - **Cost of being wrong on A:** a migration to alter the table. B is cheaper only if "per-browser" is acceptable, so Product should confirm.
   - **Blocker:** `fixture/` contains no `CREATE TABLE` and no migration mechanism. I can't see how `reports` or `users` are created, so whoever builds this must find that mechanism first.

3. **Response shape.** `render()` (`views.py:14`) is a stub that returns data. A CSV download needs a content-type and a `Content-Disposition` header, and the framework isn't visible here. Settle the response type before writing the view.

## Risks to fix in the design

- **Existing access hole.** `get_report` (`models.py:10`) takes only `report_id`, and `report_detail` (`views.py:9`) never checks the owner. Copying that pattern into the export lets any user export any report. The export should check that the report's owner is `request.user_id`, and `get_report` doesn't return `owner_id` yet. `report_detail` has the same hole today; that's a separate fix, but I'd flag it.
- **CSV formula injection.** Titles and bodies starting with `=`, `+`, `-` or `@` run as formulas in Excel. Neutralize them in `to_csv`. Use the stdlib `csv` module and write nothing by hand.
- **Pre-mortem (a year on):**
  1. History grows without bound. Accept it, since the read is capped by `LIMIT`; add pruning if the table gets large.
  2. Titles drift or reports get deleted. The title snapshot covers this.
  3. Someone adds XLSX or PDF. Add a second function then, not a seam now.

## Moves, in order

Each move lands alone with behavior unchanged elsewhere.

1. Add `owner_id` to `get_report`'s select and check it in the export path. *Proof:* a test where user B exporting user A's report gets 404.
2. Add `to_csv` with unit tests: quoting, commas, newlines, formula prefixes. *Proof:* pytest on a pure function, with no DB.
3. Create the history table (via the project's migration mechanism, once found), then `record_export` and `recent_exports`. *Proof:* record 7, read back 5, newest first, scoped to the user.
4. Add the `report_export_csv` view, wire the route and the button, and show history in `report_list`. *Proof:* an end-to-end request returns CSV with the right headers and adds one history row.

Cost: the feature touches 4 files, 2 of them new, and no existing function changes signature except `get_report`'s select.

The Asana, Atlassian, Figma, Intercom, Linear and Slack connectors need authorizing before they can be used. I didn't need them here.