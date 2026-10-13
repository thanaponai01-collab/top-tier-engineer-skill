You were partway into adding the `--since` filter. But a commit after the export was marked done broke the rounding rule the accountant confirmed, and the tests are failing now.

**What the docs say**
- `BRIEF.md`: amounts are rounded to the cent **half-up** (10.125 → 10.13) so they match the PDF invoices. The accountant confirmed this on 2026-10-02.
- `BUILD.md`: the export is marked **DONE**, with 3 tests passing on 2026-10-07. The next task is the `--since YYYY-MM-DD` filter (decided 2026-10-06).

**What happened since**
1. **2026-10-09, commit `ab7c930` "money: use standard rounding"** changed `money.py` from `ROUND_HALF_UP` to `ROUND_HALF_EVEN` (banker's rounding). That goes against invariant 1 and the accountant's decision. I ran `python -m unittest` and 2 of the 3 tests now fail:
   ```
   AssertionError: Decimal('10.12') != Decimal('10.13')
   FAILED (failures=2)
   ```
   So `BUILD.md`'s "DONE, tests OK" is out of date. Any export run since the 9th could be a cent off the PDFs on lines that end in exactly half a cent.
2. **Uncommitted `--since` work in `export.py`:** `since` is passed through `rows()` and `main()`, but only as a TODO. Nothing filters by date yet (`# TODO(--since): filter on inv["issued"] >= since; parse the date first`). There's also no CLI flag and no test for it.

**Suggested next steps**
1. Revert `ab7c930` to restore half-up rounding, then re-run the tests to confirm all 3 pass. If someone had a reason for switching to banker's rounding, it needs to go through the accountant, because the BRIEF says half-up.
2. Finish `--since`: parse the date, filter on `inv["issued"]`, add the `--since` flag and a test.
3. Update `BUILD.md` once both are done.

Should I start with the revert?