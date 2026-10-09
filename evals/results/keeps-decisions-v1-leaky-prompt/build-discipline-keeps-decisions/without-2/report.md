Slice 4 is done and the export is now JSON only. The tests pass (2 of 2) and I ran the CLI by hand. Nothing is committed (there's no git repo here anyway).

One thing went wrong along the way. A failed script run emptied `BUILD.md`. I rebuilt it from what I had read earlier. It has the same three proven rows, with the first-slice command now `out.json`, plus a new row for this slice and an updated Next section. The Deferred table was empty before and still is.

- **JSON export:** `invoices.py` no longer uses `csv`. `export()` writes a JSON array of `{id, date, customer, total}`, with `total` as a string like `"1250.00"` so it stays exact to the cent. `INV-101` is `"1250.00"` in the test.
- **Slice 4:** `python cli.py export OUT --month 2026-09` exports only that month's invoices, which is 2 of the 4 (`INV-103` and `INV-104`). A malformed month such as `2026-13` prints the usage line and exits 2. I added a `--month` test to `tests/test_export.py` and moved the old CSV test to JSON.
- **No more CSV:** `CLAUDE.md` now says the export is JSON only, that CSV was removed, and that it must not come back. In `BRIEF.md`, the old CSV decision is struck through as superseded on 2026-10-09, with a new JSON decision and the reason. `BUILD.md` records the slice as proven, with commit shown as `uncommitted`.

`BUILD.md` now says "Nothing planned" under Next. The brief doesn't suggest an obvious slice 5, so tell me what you want next, or what to add to the brief.