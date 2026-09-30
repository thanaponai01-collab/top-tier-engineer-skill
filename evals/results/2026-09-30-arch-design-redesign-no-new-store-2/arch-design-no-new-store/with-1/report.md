**Verdict: the fixture is clean, and this feature fits without restructuring.** One design decision is parked and needs a yes from you, and one existing gap needs fixing before the export ships. I wrote no code; the design is in `fixture/docs/arch-design-csv-export.md`, and its check passes (1 move, 0 broken paths).

**How to structure it** (traced by reading all four files; `fixture/` has no git history, so nothing here is measured from history):

- **CSV formatting:** a new `app/reports/export.py` with one pure function that turns a report row into CSV text. Use the stdlib `csv` module, no dependency, no plugin seam for other formats. It should neutralise cells starting with `=`, `+`, `-` or `@` so a report title can't become a spreadsheet formula.
- **Data access:** keep everything going through `app/db.py:11` (`execute`), which is the only place that runs queries. Add an owner-scoped report lookup and the history reads and writes to `app/reports/models.py`.
- **Route:** a new export view in `app/reports/views.py`. It looks up the report, formats it, records the history entry, and returns the file. Take the timestamp from the clock at this edge and pass it in, so the logic stays testable.
- **History:** a small table holding the user, report id, a snapshot of the title, and the export time. The UI reads the last N rows for the user.

**Fix first (strong finding):** `get_report` (`models.py:10-14`) looks a report up by id only. It doesn't check the owner, so an export route built on it would let any user download anyone's report. Add a separate owner-scoped lookup for the export. I left `report_detail` (`views.py:11`) alone since it's outside this request, but it has the same gap and is worth its own ticket.

**Parked, needs a yes (one-way door):** where the history lives.
- **Recommended:** a table in the existing database. It survives device changes and records what was really exported.
- **Alternative:** browser storage. It needs no schema change but is per-device and can't be trusted as a record.
- **Why it's parked:** a new table is a stored data shape, and `fixture/` has no schema or migration file, so I couldn't find where the table gets created. Tell me how tables get created here, or confirm you want the table, and I'll add that move.

**One question for product:** "download as CSV" could mean a single report or the list on the reports page. The history entry (a report title) implies a single report. That's what I designed for: `id, title, created_at, body`, with `body` as one text cell. If they want the list, the design barely changes.

The single move written to the file, Move 1, is the owner-checked lookup plus the pure formatter. It's small, two-way, and its proof is two tests: another user's report id returns nothing, and a title with a comma, quote and newline round-trips through `csv.reader`.

<!-- file written by the agent: fixture/docs/arch-design-csv-export.md -->
# ARCH-DESIGN
- at: none (fixture/ is not a git repo, so there is no sha and no change history)
- question: where do CSV export and a short export history go in app?
- yardstick: add "download as CSV" (0 modules today, would touch 3: export.py, models.py, views.py); add a column to the export (1 module: export.py); change how many past exports are shown (1 module: models.py). Source: the product request, no history to mine.
- status: open
- verdict: clean
- context: reports stay in app/reports; app/db.py stays the only place that opens the database; no web framework is visible in fixture/ so nothing below assumes one

## Finding 1: report lookup has no owner check
- where: app/reports/models.py:10, app/reports/views.py:11
- cost: 1 caller (views.py:11) reads any report by id; an export route reusing it would let any user download another user's report
- badge: strong
- evidence: traced, read both files end to end; the SELECT at models.py:11-13 filters on id only and does not select owner_id

## Move 1: add owner-checked report lookup and a pure CSV formatter
- cost: none today; without it the export leaks reports across users (Finding 1)
- pays: add a column to the export: 1 file; export route needs no new data access
- files: app/reports/models.py:10, app/reports/views.py:11
- owner: new app/reports/export.py owns turning a report row into CSV text (stdlib csv, no dependency; neutralises leading = + - @ in cells); models.py owns the owner-scoped lookup
- callers: report_detail (views.py:11) is left alone; only the new export view calls the new lookup
- door: two-way, land it and go
- proof: a test that user A exporting user B's report id gets nothing, and that to_csv on a title with a comma, quote and newline round-trips through csv.reader; both fail before, pass after; no old tests exist to replace
- effort: S
- after: nothing
