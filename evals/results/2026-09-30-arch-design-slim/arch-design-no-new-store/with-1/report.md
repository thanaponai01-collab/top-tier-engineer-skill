**Verdict: the fixture is clean, so this is a "design new" job inside `reports/`. The move that matters is a security one: `report_detail` has no ownership check, and the export must not copy that.** I read all four files in `fixture/`. That is about 40 lines, with no tests, git history, schema file or templates. All findings below are *traced*.

**How I read the request:** one CSV download per report, with the history recording each export's report title and time. A CSV of the whole reports list would have no single title to record. **Question for product:** does the button export one report, or the list? If it's the list, the history row needs a different label, and the module layout below stays the same.

### Findings that shape the design
1. **No owner check on single-report reads.** `reports/models.py:10-14` fetches by `id` only. `views.py:9-11` passes any `report_id` straight through. Only `list_reports` (`models.py:4-7`) filters by `owner_id`. An export copied from `report_detail` would let any user download, and log, any report by guessing ids. Enforce ownership in the export path.
2. **The reports table has no definition in the repo.** I found no `CREATE TABLE` or migration mechanism, so I can't see the `created_at` format or confirm that `body` is text. The history table will be the first table this repo defines, which is a one-way door (see option B below).
3. **`render` is a stub** (`views.py:14-15`), and there is no router or template. The "button" has no front-end in `fixture/`. This design covers only the endpoint and the data, and the button needs a front-end owner.
4. **`db.execute`** (`db.py:11-18`) is the single owner of DB access, and all three model functions use it. Reuse it and add no second access path.

### Structure
| Piece | Responsibility | Must never know |
|---|---|---|
| `reports/csv_export.py` (new, pure) | `report_to_csv(report) -> str` using stdlib `csv`, with spreadsheet-formula neutralising | the DB, the clock, requests |
| `reports/models.py` (+2 functions) | `record_export(owner_id, report_id, title, exported_at)` and `recent_exports(owner_id, limit=5)` | CSV, HTTP |
| `reports/views.py` (+1 view, +1 field) | `report_export(request, report_id)` does the owner check, builds the CSV, records the export, and returns the file with `Content-Disposition`. `report_list` also returns `recent_exports`. | SQL, CSV details |

Dependencies point one way: views → `csv_export` and models → `db`. The view passes `now` in, so the CSV code and history logic can be tested without the clock.

**Contracts**
- **Not found or not owned:** return the same 404 for both, so a caller can't probe which ids exist.
- **Success:** a CSV string plus a filename. Record the history row only after the CSV is built.
- **History row:** `(id, owner_id, report_id, title, exported_at)`, with `exported_at` as UTC ISO-8601.

### Two real options per choice
- **Where the code lives**
  - **A (recommended): inside `reports/`.** Export and history change when reports change, which is the same-reason test. It adds 1 new file and edits 2.
  - **B: a new `exports/` package.** It only pays off if other things get exported, and there is no second user today. That would be a guess.
- **History storage** (one-way door)
  - **A (recommended): a new `export_history` table that snapshots the title.** It answers "what did I export then", survives renames and deletes, and needs no join. The cost is a schema-creation step the repo doesn't have yet. Someone must say how tables get created (a script, `CREATE TABLE IF NOT EXISTS` at startup, or an external migration), and I can't tell from the code.
  - **B: log to a file or reuse an existing store.** I found no existing store. Files have no per-user query and are worse for "last few".
- **History size**
  - **A (recommended): `ORDER BY id DESC LIMIT 5`, no pruning.** It's one line and adds no failure mode. Rows grow unbounded but tiny.
  - **B: prune on insert.** This adds a delete to every export. Do it only if row growth is shown to matter.
- **CSV library:** stdlib `csv` (two-way door, so decided here). It gives correct quoting for free, and there's no reason for a dependency.

### Ordered moves (each lands alone)
1. **Add `csv_export.py` with tests.** The tests cover quotes, commas, newlines in `title` and `body`, and titles starting with `=`, `+`, `-` or `@` (formula injection).
   - *Proof:* `pytest` on that file.
2. **Create the `export_history` table and the two model functions. This is the one-way step, so get the creation-mechanism answer first.**
   - *Proof:* a record-then-read round-trip test, with owner isolation (user A's exports never appear for user B).
3. **Add `report_export`** with the owner check, the 404 behaviour and the history write.
   - *Proof:* an abuse-case test where user B requesting user A's report gets 404 and writes no history row. The happy path writes exactly one row.
4. **Add `recent_exports` to `report_list`.**
   - *Proof:* a test that six exports return the latest five, newest first.
5. **Front-end:** the button links to the export route. It is outside `fixture/`.

### Pre-mortem (a year on, it failed because…)
- **Another user's report got exported.** The owner check was forgotten or copied from `report_detail`. The step-3 abuse test guards this.
- **A spreadsheet ran a formula from a report title.** The neutralising lives in the pure module and is tested in step 1.
- **Large reports time out, or use too much memory.** `get_report` loads the whole `body`, and I never saw its size. I'm accepting this risk for launch. If bodies can be large, stream the response instead.
- **The history table drifted from prod.** This is unresolved until someone names the schema mechanism, and it is the step-2 blocker.

I wrote no code and no files. **Two things need an answer before step 2:** one report or the list, and how tables are created in this project.