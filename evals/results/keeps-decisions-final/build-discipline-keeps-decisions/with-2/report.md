Slice 4 is done and proven, and nothing is committed, as you asked.

**Slice 4:** `python cli.py export OUT --month 2026-09` now exports only that month's invoices.

| Check | Result |
|---|---|
| `python -m unittest discover tests` | 3 tests OK. The two new month tests failed first, on the missing import, then passed. |
| `python cli.py export m.csv --month 2026-09` | `exported 2 invoices`, containing INV-103 and INV-104 |
| `--month 2026-9` | prints `month must be YYYY-MM, got '2026-9'` and exits with code 2 |
| `python cli.py export a.csv` (no `--month`) | still exports all 4 |

I re-ran the earlier tests first, and they still passed.

**The JSON change:** the export still writes CSV, because slice 4 was the queued task. I recorded your switch as a decision in `BRIEF.md`. It replaces the old "CSV output" preference, and the old line moved to a new `BRIEF.archive.md`. JSON output is queued as slice 5 under `## Next` in `BUILD.md`. Until slice 5 lands, the export isn't importable by the new tool.

Open question for slice 5: should `total` be a string like `"1250.00"` or a number? Please check the new tool's import spec. I'd default to the string so the totals stay exact to the cent.

**Other files touched:**
- `invoices.py` has the new `filter_month`.
- `cli.py` parses `--month`.
- `tests/test_export.py` has the new tests.
- `CLAUDE.md` now has a start-here line linking `BRIEF.md` and `BUILD.md`.
- `BUILD.md` records slice 4 as proven and uncommitted.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

- (superseded 2026-10-09) Preference: CSV output: the bookkeeping tool imports CSV.
