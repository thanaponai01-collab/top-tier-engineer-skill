Slice 4 is done: `python cli.py export OUT --month 2026-09` now exports only that month's invoices. The tests pass (2 of 2). A manual run exported INV-103 and INV-104 and printed `exported 2 invoices`. An export without `--month` still writes all 4. Nothing is committed.

- **Code:** I added `invoices_for_month` in `invoices.py`, and `cli.py` now takes `--month YYYY-MM`. Any other argument shape prints the usage line.
- **Test:** `tests/test_export.py` has a new test that checks September exports exactly INV-103 and INV-104.
- **`BUILD.md`:** slice 4 is recorded as proven, with "uncommitted" in the commit column.

I did not switch the output to JSON in this slice. The export still writes CSV, so it won't import into the new bookkeeping tool yet. Your note makes the brief's CSV preference obsolete, so I made JSON output slice 5 in `BUILD.md`. I left `BRIEF.md` unchanged.

Before I build slice 5, I need two things from accounting:
- **JSON shape:** the exact structure the new tool expects.
- **Totals:** whether they should be a string like `"1250.00"` or integer cents. That choice decides whether totals stay exact to the cent.