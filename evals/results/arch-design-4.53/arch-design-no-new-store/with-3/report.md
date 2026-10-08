# Design: CSV export and export history for `fixture/`

**Outcome: design new.** This is a new feature on a small structure that is basically sound, so nothing needs replacing. **Verdict: clean.** The code is 4 files and about 45 lines. `db.py` is the one place that touches SQLite, and `reports/` follows models → views with the dependencies pointing one way. The one move that matters is to build the feature as **one pure function, one table, and two queries in the existing `reports/models.py`**. Don't add a package, a service or a plugin seam.

**Evidence:** traced. I read all 4 files in full. There is no git history, tracker or schema file in `fixture/`.

## What I found that shapes the design

1. **No owner check on `get_report`.** `reports/models.py:10` fetches by `id` only, and `report_detail` (`views.py:9`) passes no user. An export route built the obvious way (`get_report(report_id)`) would let any user download any report by changing the id. Don't copy this pattern. The export path needs an owner-scoped lookup. The existing detail view has the same hole and should be fixed separately.
2. **No schema definition.** There is no `CREATE TABLE` or migration anywhere in `fixture/`, so `reports` and `users` are created somewhere I can't see. I can't say how the new table gets created until someone tells me.
3. **`render` is a stub** (`views.py:14`, returns its input). No framework is visible, so I can't say how a response gets a CSV content type or a download filename.
4. **No clock is injected anywhere.** For one `exported_at` column that's fine, because the database can stamp it.

## Questions for product (they change the design)

- **Does the button export one report, or the whole list?** History needs "the report title", which implies one report. If the button exports the list, there is no single title and the history entry becomes "Exported all reports". I assume per-report below.
- **Which columns go in the CSV?** I assume `id, title, created_at, body`. This is a one-line change.
- **How long is "the last few"?** I assume 5.

## Structure

| Piece | Where | One-sentence responsibility | Must never know |
|---|---|---|---|
| `to_csv(report) -> str` | new `reports/csv_export.py` | Turns a report row into CSV text. | The database, the request, the clock. |
| `record_export(user_id, report)` and `recent_exports(user_id, limit=5)` | existing `reports/models.py` | Owns reads and writes of export history. | CSV formatting. |
| `report_export(request, report_id)` | existing `reports/views.py` | Checks ownership, builds the CSV, records the export, and returns the download. | SQL. |
| `report_list` | existing view | Adds `recent_exports` to what it renders, for the history panel. | Nothing new. |

Dependencies point one way: views → (`csv_export`, `models`) → `db`. The same-reason test splits CSV format from history storage. The format changes when someone asks for different columns, and the history changes when someone asks for retention or per-user views. They get different files, and `to_csv` stays testable without a database.

## Decisions

**1. Where does history live? (one-way door: stored data shape)**
- **A (recommended): a new table** `report_exports(id, user_id, report_id, report_title, exported_at DEFAULT CURRENT_TIMESTAMP)`. It stores a title snapshot, so the history stays correct if a report is renamed or deleted.
- **B: store only `report_id` and join to `reports` for the title.** This has no duplicated data, but a deleted report breaks the history row and a rename rewrites the past.
- **Forces:** the requirement is a log of what the user ran, which is A. The cost of being wrong is small and additive (one table, no change to `reports`), but it is stored data, so confirm the table-creation route first (finding 2).
- **Reuse:** `db.execute` (`db.py:11`) already owns queries. A second store, a log file or a cache would add something to back up and secure for no gain.

**2. CSV generation (two-way door)**
- **A (recommended): a pure function using stdlib `csv`.** Build the text in memory, since one report body is small.
- **B: a streaming writer.** Unneeded for a single row.
- **Safety:** prefix any cell that starts with `= + - @` with `'`. Titles and bodies are user-authored, and spreadsheets execute them as formulas when the file is opened.

**3. History written before or after the download (two-way door).** Record only after `to_csv` succeeds, so a failed export never shows up in the history. If the response fails afterward, an extra row is acceptable. This is a log, not an audit trail.

## Moves, in landing order

1. **Owner-scoped lookup** (`get_report_for_owner(report_id, owner_id)`, or an optional `owner_id` on `get_report`).
   - **Proof:** a test where user B requests user A's report and gets nothing.
   - **Payoff:** closes the hole before anything new depends on it.
2. **`csv_export.to_csv` plus tests.**
   - **Proof:** unit test on a row with commas, quotes, newlines and a `=cmd` title. No database is needed.
3. **Export-history table, `record_export` and `recent_exports`.**
   - **Proof:** a test that records 7 exports and gets back the newest 5 in order, and that user A never sees user B's.
   - **Blocked until:** product and the schema owner answer the questions above.
4. **`report_export` view, wired to a route, plus the button.**
   - **Proof:** an end-to-end request returns CSV bytes with a download header, and exactly one history row appears.
   - **Wiring check:** this move, not the earlier ones, is where "built but not connected" can happen. The route and the button are the evidence.
5. **History panel in `report_list`.**
   - **Proof:** the list response includes the last 5 exports.

**What gets cheaper:** adding a CSV column is 1 file (`csv_export.py`), and changing history retention is 1 function (`recent_exports`).

## Pre-mortem

1. **A user downloads someone else's report.** This is finding 1, handled by move 1. Make the owner check part of the definition of done.
2. **History rows grow forever.** `recent_exports` limits to 5 on read, so the UI is fine. Accepted risk: no pruning at launch, because one small row per export is negligible. Revisit if the table passes about a million rows.
3. **A formula in a title runs in a user's spreadsheet.** Handled by the cell-prefix rule in decision 2, with a test.

Nothing was written to disk. I can write this up as a file or draw the flow if you want.

**Unavailable:** the Notion, Asana, Atlassian, Figma, Intercom, Linear and Slack servers need authorization (via your claude.ai connector settings, or `/mcp` in an interactive session). I had no tracker or chat history to check for prior decisions on exports.