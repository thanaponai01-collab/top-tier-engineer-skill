Slice 4 is done: `python cli.py export OUT --month 2026-09` now exports only that month's invoices. Nothing is committed.

- **Change:** `load_invoices(month=None)` in `invoices.py` filters by `YYYY-MM`. `cli.py` accepts `--month` and rejects a malformed value with the usage message and exit code 2.
- **Test:** I added a test in `tests/test_export.py` that expects INV-103 and INV-104 for September.
- **Proof:** `python -m unittest discover tests` passes (2 tests). The CLI run wrote 2 invoices, with totals `999.00` and `3100.00`.
- **Bookkeeping:** I added the proof line to `BUILD.md`, marked "uncommitted".

**JSON:** I didn't switch the output to JSON, because that is a format change, not part of this slice. `BRIEF.md` still lists CSV as a tradeable preference. I recorded JSON in `BUILD.md` as slice 5, pending your confirmation. Before I build it, I need to know what shape the new tool expects, such as field names and whether totals are strings or numbers. A sample import file or the tool's schema would settle that. Should I update `BRIEF.md` to JSON as well?