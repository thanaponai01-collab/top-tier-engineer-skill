## Verdict

**Root cause (proven):** `parse_amount` in `parse.py:6` does `int(float(value))`, which drops the cents from every row. So `10.50, 20.25, 11.60` becomes `10, 20, 11`. That sums to **41**, when the correct total is **42.35**. The customer is short by $1.35.

The wrong value first appears in `parse.py`. `report.py` is only where it shows up, and `totals.py` adds correctly.

## Evidence

| Step | Output |
|---|---|
| Reproduce: `python report.py` | `Total: 41` |
| Raw CSV amounts, summed exactly | `['10.50', '20.25', '11.60']` → `42.35` |
| After `parse.load` | `[10, 20, 11]` ← first wrong value |
| **Cause present** (code as-is) | `Total: 41` |
| **Cause removed** (only `parse_amount` swapped for `Decimal(v)`, done in memory with no file edits) | `Total: 42.35` |

Both directions were run and the results are above. No files were changed.

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| `total()` sums wrong | Compared its input with its output | Sums `[10,20,11]` to 41 correctly | Ruled out |
| Parsing loses the cents | Printed `load()` output, then swapped only `parse_amount` | Wrong value first appears there. Removing the truncation gives 42.35 | **Proven** |

**Why it wasn't caught:** `test_totals.py` only tests `total()`, and only with whole-number amounts. Nothing tests `parse.py`, and no test runs the real CSV end to end.

## Minimal repro (to use as the regression test)

```python
from parse import parse_amount
from report import render

def test_parse_keeps_cents():
    assert parse_amount("10.50") == Decimal("10.50")

def test_report_total_matches_csv():
    assert render("data.csv") == "Total: 42.35"
```

## Suggested fix (not applied)

In `parse.py`, change it to `from decimal import Decimal` and `return Decimal(value)`. Avoid `float`, because it introduces rounding errors with money. Then add the two tests above.

One decision is yours: should the report always show two decimal places (`42.35`, and `42.00` rather than `42`)? If yes, format the total in `render` as `f"{...:.2f}"`. Tell me and I'll apply the fix with the tests.