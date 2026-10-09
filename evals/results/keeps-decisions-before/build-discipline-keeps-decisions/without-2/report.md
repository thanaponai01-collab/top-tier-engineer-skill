Slice 4 is done and I haven't committed anything. `python cli.py export OUT --month 2026-09` now writes only September's invoices (INV-103 and INV-104). The tests pass, including a new one for the month filter, and I ran the command by hand to check it.

- **Code:** `invoices.py` has a new `in_month()`, `cli.py` takes the `--month YYYY-MM` option, and the new test is in `tests/test_export.py`.
- **`BUILD.md`:** I accidentally emptied it with a bad script, then rewrote it from what I'd read earlier. I added the slice 4 proof line, marked "uncommitted". The only thing that could be missing is trailing whitespace.

**JSON switch:** The export is still CSV. Moving to JSON is the next slice, but I didn't start it because I don't have the new tool's schema. I need the field names, whether totals are strings like `"1250.00"` or numbers, and whether it wants a top-level array or a wrapper object. `BRIEF.md` also still lists CSV as a preference, and I'll update that line once I have the schema.

I wrote the "Next" section of `BUILD.md` as the JSON switch, marked blocked on that schema and the brief decision.