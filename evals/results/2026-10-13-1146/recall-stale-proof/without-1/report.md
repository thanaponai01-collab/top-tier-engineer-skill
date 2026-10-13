The export is done, but a commit on Oct 9 broke it, and the `--since` filter is only stubbed out.

**What's finished**
- Invoice export was built on Oct 3 with half-up rounding. It was marked proven on Oct 7 with 3 tests passing.

**What broke**
- Commit `ab7c930` (Oct 9, "money: use standard rounding") changed `money.py` from `ROUND_HALF_UP` to `ROUND_HALF_EVEN`.
- That contradicts `BRIEF.md`. Invariant 1 and the Oct 2 decision (confirmed by the accountant) require half-up so the export matches the PDF invoices to the cent.
- `python -m unittest` now fails: 2 of 3 tests fail. One example is 10.125 giving 10.12 instead of 10.13. `BUILD.md` still says "DONE, 3 tests OK", which is no longer true.

**What's in progress**
- `export.py` has uncommitted edits. They add a `since=None` parameter to `rows()` and `main()`, plus a TODO to filter on `inv["issued"] >= since` after parsing the date.
- The filtering isn't written, and the `--since` command-line flag doesn't exist yet. That's the "Next" item in `BUILD.md`, from the Oct 6 decision.

**Suggested next steps**
1. Revert the rounding in `money.py` to `ROUND_HALF_UP`. I haven't touched it. Unless you have a newer decision from the accountant, the brief says half-up.
2. Finish `--since`: parse the date, filter invoices, and add the flag and a test.
3. Update `BUILD.md` once the tests pass again.

Do you want me to go ahead with all three? Or did you switch to banker's rounding on purpose?