**Verdict: clean.** `fixture/` is 4 small files with one clear data-access owner. Nothing needs restructuring first. The one move that pays most is to add the feature inside `app/reports/` and reuse `app.db.execute`. Don't add a new service, layer or datastore.

**Outcome chosen: design new, inside the existing structure.** You can override this. I read all 4 files. There is no git history, so nothing here is checked against past decisions.

## What exists
- `app/db.py:11` `execute()` is the single query owner. Every model goes through it.
- `app/reports/models.py:4` `list_reports(owner_id)` and `:10` `get_report(report_id)` are the reads.
- `app/reports/views.py:4,9` are the two views. `render()` at `:14` is a stub, so I can't see how responses, headers or routing work. That is **suspected**, not traced.
- The schema and migrations aren't in the fixture, so I can't see how tables are created.

## Module boundaries
| Piece | Where | Responsibility (one sentence) | Must never know |
|---|---|---|---|
| CSV formatting | new `reports/export.py` | Turns report rows into CSV text (stdlib `csv`, a pure function) | The DB, the request |
| Export history | `reports/models.py`, new functions | Records and lists a user's exports | CSV formatting |
| Download view | `reports/views.py`, new `report_export_csv` | Checks access, calls export, records history, returns the file | SQL |
| History display | `report_list` view | Includes the last N exports with the report list | — |

Calls go one way: views → models and export → `db`. `export.py` doesn't import `db`, so you can test it without a database. Don't create a separate `exports/` package. It would be a second owner for report data, and its history would change for the same reasons as reports.

## Two options per choice

**1. History storage (one-way door: a stored data shape).**
- **A (recommended):** a table `report_exports(id, user_id, report_id, report_title, exported_at)`. It is the simplest thing that survives a restart, and it reuses `db.execute`.
- **B:** keep history in the session or browser storage. It needs no schema change, but it disappears on logout or device change and is hard to test. This only works if "last few exports" can mean "this session".
- **The decision for you:** store a title snapshot or join to `reports.title`. A snapshot keeps the history readable if the report is renamed or deleted. A join avoids duplicating data. I recommend the snapshot because the history is a record of what was exported. Use UTC for `exported_at`. I can't check what format `created_at` uses, so match it once someone looks at the schema.
- **Cost if wrong:** a migration plus a backfill. History rows can't be reconstructed afterward. Get sign-off before the table is created.

**2. What gets exported (needs an answer from Product).**
- **A:** the report list, meaning `list_reports` columns (id, title, created_at).
- **B:** one report's `body`.
- "Report title" in the history suggests per-report export, but "on the reports page" suggests the list. This changes the route and the CSV shape. I couldn't settle it from the code.

**3. Trimming history (two-way door).** Query `ORDER BY id DESC LIMIT 10` per user and don't prune stored rows at launch. Add pruning only if the table actually grows.

## Problems to fix before this ships
- **Missing ownership check.** `get_report` (`models.py:10-14`) filters only by `report_id`. `report_list` is owner-scoped but `report_detail` isn't. A per-report export built on it would let any user download any report by changing the id. Add an `owner_id` parameter, or make the export read owner-scoped.
- **CSV injection.** Titles and bodies are user text. A cell starting with `=`, `+`, `-` or `@` becomes a formula in Excel. `export.py` should prefix such cells with `'`, and that rule needs a test.

## Moves, in landing order
1. **Settle the open questions.** Which export (list or single), snapshot or join, and where tables are created. Proof: written answers in the ticket.
2. **Owner-scoped read.** Fix `get_report` or add a scoped variant. Proof: a test that user B gets `None` for user A's report. This is useful on its own and can ship alone.
3. **`reports/export.py`.** A pure `to_csv(rows, columns)` that handles quoting, commas and newlines in titles, and formula prefixes. Proof: unit tests with no DB.
4. **History table plus `record_export` and `recent_exports(user_id, n)`.** The migration is a one-way door, so it needs your sign-off. Proof: round-trip test, and `recent_exports` returns the newest 10 in order.
5. **`report_export_csv` view.** Check access, build the CSV, record history after the CSV builds successfully, then return the file. Recording only after success avoids history entries for failed exports. Proof: a request test checks the content-type, the filename header and one history row per export.
6. **Button and history list on the reports page.** Proof: the page lists the latest exports, and a manual click downloads the file.

## Pre-mortem (a year on, it failed because…)
1. **Someone downloaded another user's report.** Mitigated by move 2 and its test.
2. **Titles were wrong or missing in the history after renames or deletes.** Mitigated by the snapshot option.
3. **Large exports timed out or ran out of memory.** `execute()` does `fetchall()` (`db.py:16`). That is fine at launch scale; accepted risk. Revisit with streaming if a report exceeds a few thousand rows.

**Not covered:** I couldn't check the routing, auth middleware or schema setup, because none are in `fixture/`. The ownership gap above only matters if `report_detail` is reachable without a separate permission check elsewhere.