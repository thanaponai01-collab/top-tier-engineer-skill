Slice 4 is done. `python cli.py export OUT --month 2026-09` now exports only that month's invoices (2 of 4). Both tests pass, and I ran the command by hand: it wrote INV-103 and INV-104, and leaving out `--month` still exports all 4. Nothing is committed.

- **Code:** I added `invoices_in_month` in `invoices.py` and the `--month` option in `cli.py`. I also added a test for the month filter.
- **Bad arguments:** the CLI prints the usage text and returns 2 for any argument shape other than `export OUT` or `export OUT --month YYYY-MM`.
- **`BUILD.md`:** I added the proof line for this slice, marked "uncommitted".

**JSON:** the export still writes CSV, which the new bookkeeping tool can't import. I didn't switch it, because it changes the existing test and I don't know the JSON shape the tool expects. I made it Slice 5 under Next in `BUILD.md`. I left `BRIEF.md` alone, so its CSV preference is still the old one.

Do you know the JSON shape the tool wants (field names, and whether totals are strings like `"1250.00"` or numbers)? Slice 5 needs it first.