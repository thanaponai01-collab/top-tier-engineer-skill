Slice 4 is done: `python cli.py export OUT --month 2026-09` now exports only September's invoices, which is 2 of the 4 (INV-103 and INV-104).

I ran the tests and both pass. I also ran the command by hand and got `exported 2 invoices`. A bad month such as `2026-13` prints the usage line and exits with code 2.

The changes:
- **`invoices.py`:** a new `in_month` filter.
- **`cli.py`:** the `--month` option, with the month format checked.
- **`tests/test_export.py`:** a new test for the filter.
- **`BUILD.md`:** slice 4 marked proven, with "uncommitted" in the commit column.

**The JSON change:** I didn't switch the output, and the export still writes CSV. `BRIEF.md` lists CSV as a tradeable preference, and I don't know what structure the new tool expects. It could be a flat array, a wrapper object, totals as strings or numbers, or something else. I made "switch the export to JSON" the next slice in `BUILD.md`. Once you confirm the shape, I'll update `BRIEF.md` and `export`.