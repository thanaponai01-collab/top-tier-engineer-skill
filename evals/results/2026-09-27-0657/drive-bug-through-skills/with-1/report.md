It's fixed: `python report.py` now prints **`Total: 42.35`** instead of `Total: 41`. The customer was right. Every amount was losing its cents.

**Cause (proven):** `parse_amount` in `parse.py:6` did `int(float(value))`, so 10.50, 20.25 and 11.60 became 10, 20 and 11. I tested it both ways. With that line in place the report says 41. With only the cut-off removed, the same data gives 42.35. The adding-up code (`totals.py`) and the printing code (`report.py`) were fine. Nothing caught this because the only tests passed whole numbers to `total()`.

**Fix:** `parse_amount` now returns `Decimal(value)`, a two-line change. I used `Decimal` rather than `float` so amounts like 0.10 + 0.20 come out as exactly 0.30, with no rounding error. `load` is its only caller, and `load` is only called by `report`.

**How I know it holds (proven, all run):**
- **New test file:** `test_report.py` checks that parsing keeps the cents, that a full report on this data prints `Total: 42.35`, and that 0.10 + 0.20 prints `0.30`.
- **Before and after:** all 3 new tests failed on the old code and pass on the new. The whole suite passes: 5 of 5, and the 2 old tests are unchanged.
- **Deliberate breakage:** I broke the parser 4 ways on purpose: the old `int(float())`, plain `float`, rounding to whole units, and rounding to one decimal place. The tests failed every time. I then put the fixed file back and the suite passes again.

**Two things you might want to decide:**
- **Bad amounts raise a different error.** An empty or non-numeric amount now raises `decimal.InvalidOperation` instead of `ValueError`. Nothing in this code catches either one, but anything outside it that catches `ValueError` would no longer catch this.
- **Scientific notation prints oddly.** If the CSV ever had an amount like `1e2`, it would print as `1E+2`. The current data has none, so I didn't change how totals are printed.

I also didn't check whether statements the customer already received need correcting. That's a business call, not a code change.

**Files:** `parse.py` (the fix), `test_report.py` (new tests), and `DRIVE.md` (my working checklist, all steps ticked; delete it if you don't want it). This folder isn't a git repository, so nothing was committed.

<!-- file written by the agent: fixture/DRIVE.md -->
# DRIVE — statement total short

EXIT CHECK: `python report.py` prints `Total: 42.35` (10.50+20.25+11.60), a regression test
through parse→total→render fails before the fix and passes after, and existing tests stay green.
Budget: ~6 steps, stop at 12.

- [x] debug-protocol — root cause proven by a failing repro
- [x] evolve-maintain — smallest fix where all callers route through; repro passes
- [x] correctness-gate — full test suite + report.py output checked

DONE 2026-09-27: cause = parse.py int(float()) truncated cents; fix = Decimal; guarded by test_report.py; report prints Total: 42.35.
