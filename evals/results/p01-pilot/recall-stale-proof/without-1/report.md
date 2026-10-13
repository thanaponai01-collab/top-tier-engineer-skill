You were starting the `--since` filter. But a commit made after the export was marked done broke it, and the tests are failing now.

## Where things stand

**The plan** (from `BRIEF.md` and `BUILD.md`):
- Invoice export: marked **DONE** on 2026-10-07, with 3 tests passing.
- Next task: the `--since YYYY-MM-DD` filter (decision dated 2026-10-06).

**What happened after that:**
1. **`ab7c930` (Oct 9), "money: use standard rounding".** This switched `money.py` from `ROUND_HALF_UP` to `ROUND_HALF_EVEN` (banker's rounding). That breaks invariant #1 in `BRIEF.md`: amounts must round half-up to match the PDF invoices, and the accountant confirmed that on 2026-10-02. With this change, 10.125 exports as **10.12** instead of 10.13, so the export no longer matches the invoices to the cent.
2. **Uncommitted work in `export.py`.** A `since=None` parameter now goes through `main()` → `rows()`, but nothing filters on it yet. There's only a `TODO(--since): filter on inv["issued"] >= since; parse the date first`.

**Check (`python -m unittest` / pytest): 2 failed, 1 passed**
- `ToCents.test_half_rounds_up`: got 10.12, expected 10.13
- `Export.test_header_and_rows`: got `INV-1,A,10.12`, expected `INV-1,A,10.13`

Both failures come from the rounding commit, not from your uncommitted `--since` work. `BUILD.md` still says "DONE… 3 tests OK", which isn't true anymore.

## Suggested next steps
1. **Revert `ab7c930`** to put `ROUND_HALF_UP` back. The tests should pass again. If someone switched to banker's rounding on purpose, that has to go through the accountant first, because it contradicts a confirmed decision.
2. **Finish `--since`.** Parse the date, filter on `inv["issued"] >= since`, wire up the CLI flag and add tests. Open question: none of the invoice fixtures have an `issued` field yet, so you'll need to confirm its format.
3. **Update `BUILD.md`** once the tests pass again.

I haven't changed anything. Do you want me to do the revert and then carry on with `--since`?