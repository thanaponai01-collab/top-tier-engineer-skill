The export now writes JSON only, and slice 4 (`--month`) is done. I haven't committed anything.

**Tests and checks**
- The two tests pass with `python -m unittest discover tests`.
- `python cli.py export OUT --month 2026-09` exported 2 invoices, INV-103 and INV-104.
- `--month 2026-13` prints the usage line and exits with code 2.

**What changed**
- **CSV removal:** `invoices.py` no longer imports `csv`.
- **Output format:** the file is a JSON array of `{id, date, customer, total}`. `total` is a string such as `"1250.00"`, built from integer cents so there's no float rounding. If the new tool needs `total` as a number, say so.
- **Month filter:** `load_invoices(month)` and `cli.py` take `--month YYYY-MM` and reject malformed values.
- **Tests:** `tests/test_export.py` now reads JSON and has a new month-filter test.

**Keeping CSV out**
- **`BRIEF.md`:** the CSV decision is struck through and a new 2026-10-09 entry says JSON only, never reintroduce CSV. The cents invariant now refers to the JSON `total` field.
- **`CLAUDE.md`:** it now has a line stating the same rule, since that file is read every session.
- **`BUILD.md`:** it notes that the older proof rows were proven against CSV. "Next" now says nothing is planned, so the next slice needs your pick.

A script error emptied `BUILD.md` partway through. I rewrote it from what I'd read earlier, so it should match the original apart from my edits. Nothing is under version control, so check it if it matters.