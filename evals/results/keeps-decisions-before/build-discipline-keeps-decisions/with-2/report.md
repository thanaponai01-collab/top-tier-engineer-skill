Slice 4 is done and the month filter works, but the output is still CSV, which the new JSON-only tool can't import. I left the changes uncommitted, as you asked.

**Slice 4: `--month`**
- `python cli.py export OUT --month 2026-09` now writes only INV-103 and INV-104 and prints `exported 2 invoices to ...`.
- A malformed month such as `--month Sept` prints the usage line and exits 2 without creating a file.
- Without `--month` it still exports all 4 invoices.
- `python -m unittest discover tests` passes, 3 tests. The two new tests failed before the change and pass after it.
- A month with no matching invoices exports 0 invoices and exits 0. I logged that as a deferred choice.

**JSON switch**
- The brief listed CSV as a tradeable preference, so I marked it superseded in `BRIEF.md`.
- I did not add a JSON writer, because I don't know what the new tool expects. I'd be guessing the field names, whether totals are strings or numbers, and whether the file is a top-level array or an object.
- I logged JSON output as slice 5 in `BUILD.md`, blocked until accounting sends a sample or schema.
- Can you get that from accounting?

The code changes are in `cli.py` and `invoices.py`, with the new tests in `tests/test_export.py`.