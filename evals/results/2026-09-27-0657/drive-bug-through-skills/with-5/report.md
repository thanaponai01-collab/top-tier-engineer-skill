It's fixed and I've checked it: `python report.py` now prints `Total: 42.35`, which matches adding up `data.csv` by hand (10.50 + 20.25 + 11.60).

**Cause:** `parse_amount` in `parse.py` did `int(float(value))`, which dropped the cents from every row before adding them up. That turned the total into 10 + 20 + 11 = 41, so the statement was short by 1.35. The adding-up code in `totals.py` was fine. Its tests only used whole numbers, so they never caught this.

**Fix:** `parse_amount` now returns `Decimal(value)`, a change of two lines in `parse.py`. I used `Decimal` instead of `float` because float sums can drift for money, even though float happens to give the right answer for this data. Only `load` calls `parse_amount`, and `load` feeds every amount into the total, so this one change covers all of them.

**How I know:**
- **Regression test:** I added `test_report.py`, which reads a CSV with cents through `load` → `total` → `render`. Before the fix it failed with `41 != Decimal('42.35')`, the customer's number. After the fix, all 3 tests pass.
- **Mutation check:** I deliberately broke the code 5 ways (the old truncation, two kinds of rounding, dropping the first row, dropping the last row). The tests caught all 5. I then restored the files and diffed them to confirm they were back to the fixed version.

**Two side effects of the fix, which I haven't changed:**
- A bad or empty amount now raises `decimal.InvalidOperation` instead of `ValueError`. Nothing in the code catches either one.
- An amount written like `1e2` would print as `1E+2` rather than `100`.

I only ran this locally on the fixture. Any statements already sent out were also truncated and would need to be reissued; that's for you to decide. The steps and these notes are in `DRIVE.md`.

<!-- file written by the agent: fixture/DRIVE.md -->
# Drive: statement total is short

Exit check: `python report.py` prints `Total: 42.35` for data.csv, and a regression test that failed
before the fix now passes, alongside the existing tests. Budget: ~5 steps, stop at 10.

- [x] Root cause (traced): parse.py `parse_amount` = `int(float(value))` truncates cents -> 41.
- [x] Regression test on the real path (load + total with cents) fails before the fix.
- [x] Fix in parse_amount (single entry point for all amounts); use Decimal, not float, for money.
- [x] correctness-gate: all tests green, report prints `Total: 42.35`.

Result: PASS. 3/3 tests green; report prints Total: 42.35; 5/5 mutations caught.
Open: bad amounts now raise decimal.InvalidOperation (was ValueError; no caller catches either);
exponent input like 1e2 would render as 1E+2.
