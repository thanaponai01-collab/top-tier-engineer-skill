Slice 4 is done and proven: `--month` now works, but the export still writes CSV. Nothing is committed.

**Slice 4**
- `python cli.py export OUT --month 2026-09` exports 2 of the 4 invoices (INV-103 and INV-104).
- `--month sep` prints the usage text and exits with code 2.
- `python -m unittest discover tests` passes with 4 tests. I confirmed the 3 new ones failed before I wrote the code.
- Changes are in `invoices.py` (`load_invoices(month=None)`), `cli.py` (flag parsing and month validation) and `tests/test_export.py`.

**JSON decision**
- I recorded the switch to JSON in `BRIEF.md` (Preferences #1) and moved the old CSV line to a new `BRIEF.archive.md`.
- I did not change the output format. You asked for the next slice, and the month filter doesn't depend on the format.
- Slice 5 is queued in `BUILD.md` under `## Next`: switch the output to JSON. It needs the new tool's import spec first: field names, and whether `total` is a string or a number.
- Until that lands, the export still writes CSV, so accounting can't import it yet.

I also added a start-here block to `CLAUDE.md` linking `BRIEF.md` and `BUILD.md`, and logged the slice in `BUILD.md` as uncommitted.

Can you send the new tool's import spec, or a sample file it accepts?

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

Superseded lines, moved verbatim from BRIEF.md.

- (Preferences 1) CSV output: the bookkeeping tool imports CSV. — superseded 2026-10-09: accounting switched tools; the new one takes JSON.
