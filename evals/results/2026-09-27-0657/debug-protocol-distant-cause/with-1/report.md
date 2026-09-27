The total is short because of `parse.py:6`. `parse_amount` does `int(float(value))`, which drops the cents from every row before anything is added up. The real total is **42.35**, and the report prints **41**, so it's short by 1.35. I proved this by running it both ways.

**Where it goes wrong:** `report.py` is only where the wrong number shows up. The amounts are already wrong by the time `load()` returns them:
```
raw CSV:     10.50, 20.25, 11.60   → sum 42.35
parsed rows: 10,    20,    11      → sum 41
```
`totals.total` adds correctly. It's just being given whole numbers.

**Proof, both ways:**
| Condition | Command | Output |
|---|---|---|
| Truncation left in | `python report.py` | `Total: 41` |
| Only truncation removed (temporarily swapped `parse.parse_amount` for `Decimal(v)`, no file edited) | `report.render()` | `Total: 42.35` |

**What I tested:**
| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| `total()` adds wrong | Compared parsed rows with a sum of the raw CSV | The rows are already whole numbers | Ruled out |
| `parse_amount` cuts off the cents | Swapped in a parser that keeps cents | 42.35 | **Proven** |

**Why the tests didn't catch it:** `test_totals.py` only passes whole numbers straight into `total()`. Nothing tests `parse_amount`, and nothing runs the full path from the CSV to the printed total. The tests pass (`OK`) even with the bug.

**Regression test to add (it fails right now):**
```python
from decimal import Decimal
from report import render
from parse import parse_amount

def test_parse_keeps_cents():
    assert parse_amount("10.50") == Decimal("10.50")

def test_report_total_matches_csv():
    assert render("data.csv") == "Total: 42.35"
```

**Suggested fix (not applied):** in `parse.py`, change `parse_amount` to return `Decimal(value)` and import `Decimal`. Use `Decimal` rather than `float` so money doesn't pick up rounding errors. I haven't changed any files: this was a diagnosis, and the fix changes what the report prints (`41` becomes `42.35`), so you should agree on that format first. Say the word and I'll apply it along with the tests above.