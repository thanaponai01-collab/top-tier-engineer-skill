Slice 4 is done and proven, but not committed, as you asked. `python cli.py export OUT --month 2026-09` now exports only that month's invoices. The output is still CSV for now.

| Slice | Proof | Status |
|---|---|---|
| 4: month filter | 3 unit tests pass. `--month 2026-09` → `exported 2 invoices`, with INV-103 and INV-104 only. `--month 2026-13` prints usage and exits 2. A month with no invoices returns an empty list. | proven, uncommitted |

I re-ran the earlier test first (green) and wrote the new tests before the code, so they failed first. The change touched `invoices.py` (`load_invoices(month=None)`), `cli.py` (parses `--month`) and `tests/test_export.py`.

**JSON decision:** I recorded your JSON change in `BRIEF.md` as Decision 1, and it replaces the CSV preference. The old CSV line moved to the new `BRIEF.archive.md`. I also added a start-here block to `CLAUDE.md` linking `BRIEF.md` and `BUILD.md`.

**Open question on the JSON shape:** I assumed a JSON array of objects with the same fields as the CSV columns, with `total` as a string like `"1250.00"` to keep cents exact. That assumption is in the brief. If accounting has an import spec for the new tool, send it and I'll match it.

**Next:** Slice 5 switches the export to JSON, replacing CSV. It's queued in `BUILD.md`, since the output format is a separate change from the month filter.

<!-- file written by the agent: fixture/BRIEF.archive.md -->
# Brief archive

Superseded lines, moved verbatim from BRIEF.md.

- (Preferences 1) CSV output: the bookkeeping tool imports CSV. — superseded 2026-10-09: new bookkeeping tool takes JSON.
