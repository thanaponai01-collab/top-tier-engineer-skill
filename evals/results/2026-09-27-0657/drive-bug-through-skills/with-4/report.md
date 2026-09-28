The total is fixed: `python report.py` now prints **`Total: 42.35`**, which matches 10.50 + 20.25 + 11.60 added by hand. A new end-to-end test failed before the fix and passes after it.

**Cause (proven):** `parse_amount` in `parse.py` did `int(float(value))`, which cut the cents off every row, so the report summed 10 + 20 + 11 = 41. The adding in `totals.py` was fine. The existing tests missed it because they only give `total()` whole numbers and never read real CSV data.

**Fix:** `parse_amount` now returns `Decimal(value)`. It was two lines in `parse.py`, and `load` is its only caller. I used `Decimal` because it's exact for money. `float` happens to give 42.35 for this data, but it can drift: 0.10 + 0.20 comes out as `0.30000000000000004`.

**What I ran (proven):**
- `test_report.py` (new) runs the real flow from the CSV to the printed line and expects `Total: 42.35`. It failed before the fix and passes after.
- `test_totals.py` passes before and after.
- `python report.py` prints `Total: 42.35`.

**Not checked:**
- The total prints with as many decimal places as the data gives it. An amount written as `10.5` could produce a total like `42.3` rather than `42.30`. If statements need exactly two places, format it in `render`.
- A blank or badly formed amount now raises a `decimal.InvalidOperation` error instead of a `ValueError`.
- Only `data.csv` was tested. I don't have the customer's actual statement data.

**Process:** I ran the debug → fix → verify steps directly rather than loading each sub-skill. The steps and result are recorded in `fixture/DRIVE.md`. Nothing was deployed, and this isn't a git repo, so nothing was committed.

<!-- file written by the agent: fixture/DRIVE.md -->
# DRIVE: statement total is short

Exit check: `python report.py` prints `Total: 42.35` (10.50+20.25+11.60, done by hand) AND a test that
goes through parse->total fails before the fix and passes after; existing tests stay green.
Budget: ~5 steps, stop at 10.

- [x] debug-protocol: root cause proven by a run (not just by reading)
- [x] evolve-maintain: smallest fix where every caller routes through; regression test red->green
- [x] correctness-gate: full suite + report.py output checked against the hand total

## Result
Cause (proven): parse.parse_amount did int(float(v)), truncating cents -> 10+20+11 = 41.
Fix: parse_amount returns Decimal(v). test_report.py red before, green after; test_totals.py green both.
report.py now prints `Total: 42.35`.
