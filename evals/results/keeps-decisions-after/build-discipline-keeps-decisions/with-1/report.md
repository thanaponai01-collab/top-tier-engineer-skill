Slice 4 is done and proven, but not committed, as you asked. `export` now takes `--month`, and the export still writes CSV.

| Slice | Proof | Status | What you can do now |
|---|---|---|---|
| 4 | `python cli.py export o.csv --month 2026-09` → `exported 2 invoices` (INV-103, INV-104) | proven, uncommitted | Export a single month's invoices |

- **Tests:** `python -m unittest discover tests` shows 3 tests passing, including two new ones: the month filter and a bad-month rejection.
- **Bad input:** `--month 2026-9` prints `month must be YYYY-MM, got '2026-9'` and exits with code 2.
- **No `--month`:** the old behavior is unchanged, so all 4 invoices export.
- **JSON switch:** I recorded it in `BRIEF.md`. The CSV preference now reads JSON, with a dated line under a new `## Decisions` section, and the old CSV line is in `BRIEF.archive.md`. I did not build JSON output yet.
- **Next slice:** JSON output is queued as slice 5 in `BUILD.md`. Before building it, I need the field layout the new bookkeeping tool expects (field names, and whether totals are strings or numbers). I'll hold off on guessing it.
- **Project files:** I added a start-here line to `CLAUDE.md` linking `BRIEF.md` and `BUILD.md`.

The changed files are `invoices.py`, `cli.py`, `tests/test_export.py`, `BUILD.md`, `BRIEF.md` and `CLAUDE.md`. `BRIEF.archive.md` is new.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

- Superseded 2026-10-09: "CSV output: the bookkeeping tool imports CSV."
