I found and proved the cause. `parse_amount` in `parse.py:6` runs `int(float(value))`, which cuts the cents off every amount before anything gets added up. The sum itself is correct, so the problem appears in `report.py` but starts in `parse.py`. I didn't change any files; all experiments patched the code in memory.

**Failure:** `python report.py` prints `Total: 41`. The amounts in `data.csv` (10.50 + 20.25 + 11.60) should total **42.35**.

**Proven cause:** `int()` drops the fractional part of each amount. 10.50 becomes 10, 20.25 becomes 20 and 11.60 becomes 11, which is 41. That's 1.35 short.

**Why it wasn't caught:** `test_totals.py` only tests `total()`, using whole-number inputs it writes itself. Nothing tests `parse.py`, and no test runs the full path from the CSV file to `render()`. The tests passed (E1) while the bug was live. There's no git history here, so I couldn't check why `int` was used.

### Experiments

| # | Hypothesis / question | Experiment | Result | Verdict |
|---|---|---|---|---|
| E0 | Can I reproduce it? | `python report.py` | `Total: 41` | Reproduced |
| E1 | Do the existing tests catch it? | `python -m unittest test_totals` | OK | They don't: no coverage of parsing or the full path |
| E2 | Where does the bad value first appear? | Compare raw CSV values with `load()` output | raw `['10.50','20.25','11.60']` → parsed `[10, 20, 11]` | Bad value first appears in `parse.py` |
| E3 | Is `totals.py` at fault? | `total()` on exact Decimal inputs | `42.35` | Ruled out: summing is correct |
| E4 | Smallest repro | `parse_amount('10.50')` | `10` | One call reproduces it |
| E5 | **Cause removed:** swap only `parse_amount` for `Decimal(v)`, in memory | `report.render()` | `Total: 42.35` | Failure goes away |
| E5b | **Cause present:** original code, same input | `report.render()` | `Total: 41` | Failure returns. Proven both ways |

### Proposed regression test (not added)
```python
from decimal import Decimal
from parse import parse_amount
from report import render

def test_parse_keeps_cents():
    assert parse_amount("10.50") == Decimal("10.50")

def test_report_total_matches_statement():
    assert render("data.csv") == "Total: 42.35"
```
Both tests fail on the current code (`10` and `Total: 41`).

When you fix it, parse amounts with `Decimal(value)` rather than `float`, because floats would bring in rounding errors on money. Check how the existing whole-number tests in `test_totals.py` behave after the change. You only asked for a diagnosis, so I haven't made the fix or added the test. I can do both if you want.