Slice 4 is done and proven: `python cli.py export OUT --month 2026-09` now exports only that month's invoices. The export is still CSV, so it doesn't yet match the new JSON requirement. Nothing is committed.

Before starting, I re-ran the previous slice's tests and they passed.

**Proof**
- **Tests:** I wrote the new tests first and they failed. After the change, `python -m unittest discover tests` gives 4 tests, OK.
- **Real run:** `python cli.py export o.csv --month 2026-09` printed `exported 2 invoices` and wrote INV-103 and INV-104.
- **Error path:** `--month sept` prints the usage line and returns 2, and so does a bare `--month` with no value. This is covered by a test.

**Changes**
- `invoices.py`: `load_invoices(month=None)` filters by `YYYY-MM`.
- `cli.py`: parses and validates `--month`.
- `tests/test_export.py`: three new tests.

**JSON switch**
- **Brief:** I recorded it in `BRIEF.md` under a new `## Decisions` section and changed the output preference to JSON. The old CSV line is in `BRIEF.archive.md`.
- **Not built yet:** I didn't switch the output in this slice, because it's a separate change. It is slice 5 under `## Next` in `BUILD.md`.
- **Question for you:** should `total` be a string like `"1250.00"` or a number? That depends on what the new tool accepts, and I noted it in `BUILD.md`.

**Housekeeping:** `CLAUDE.md` had no start-here block, so I added links to `BRIEF.md` and `BUILD.md`. `BUILD.md` lists slice 4 as uncommitted.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

## Superseded 2026-10-09
- Preferences 1: CSV output: the bookkeeping tool imports CSV. (Accounting switched tools; the new one takes JSON.)
