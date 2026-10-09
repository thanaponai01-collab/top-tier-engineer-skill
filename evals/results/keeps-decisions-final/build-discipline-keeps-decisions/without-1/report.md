Slice 4 is done: `python cli.py export OUT --month 2026-09` now exports only that month's invoices. I checked it by running it and it printed `exported 2 invoices` (INV-103 and INV-104). The unit tests pass, and running without `--month` still exports all 4. Nothing is committed.

I added `in_month()` in `invoices.py` and the `--month` argument in `cli.py`. I also added a test for the filter. In `BUILD.md` I marked the slice proven with "uncommitted" in the commit column.

**JSON output:** the export still writes CSV. I didn't switch it because I don't know what the new tool expects. I need two things from you:
- **Field names:** whether the new tool wants the same ones (`id`, `date`, `customer`, `total`) or different ones.
- **Total format:** whether `total` should be a number or the string `"1250.00"`. A JSON number would lose the exact-to-the-cent guarantee in the brief, so I'd lean toward the string.

I made JSON output the next slice in `BUILD.md`, marked blocked until you answer those two. I haven't edited `BRIEF.md`, which still lists CSV as a preference, so say if you want it updated.