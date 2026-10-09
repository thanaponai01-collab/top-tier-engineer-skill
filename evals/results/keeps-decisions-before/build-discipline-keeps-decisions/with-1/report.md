Slice 4 is done: `python cli.py export OUT --month 2026-09` now exports only that month's invoices. It still writes CSV, which the new tool can't import. I haven't committed anything.

The suite passes (3 tests). I ran the command by hand and it gave:
```
exported 2 invoices
id,date,customer,total
INV-103,2026-09-02,Ardent Ltd,999.00
INV-104,2026-09-19,Corvo GmbH,3100.00
```
A bad month (`--month 2026-13`) prints `bad month '2026-13', expected YYYY-MM`, exits with code 2 and writes no file. The changes are in `invoices.py`, `cli.py` and `tests/test_export.py`, and I recorded the slice in `BUILD.md` as uncommitted.

**Output format.** The brief says the output must be CSV because the bookkeeping tool imports CSV. That's out of date now that accounting uses a tool that takes JSON. I didn't switch the output, because I don't know what JSON the tool expects. I put it in `BUILD.md` as slice 5, blocked on that, and I haven't edited `BRIEF.md` yet. To unblock it I need:
- a sample or spec of the import file;
- the top-level shape (a list of invoices, or an object wrapping one);
- whether totals are cents or decimal strings.

Once I have those, I'll add the JSON output and update the brief.