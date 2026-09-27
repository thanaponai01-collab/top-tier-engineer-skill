**Root cause (proven):** `parse_amount` in `fixture/parse.py:6` does `int(float(value))`, which cuts the cents off every amount. 10.50, 20.25 and 11.60 become 10, 20 and 11, so the report prints `Total: 41`. It should be **42.35**, so the customer is short by 1.35. `totals.py` and `report.py` are correct; they just add up numbers that are already wrong.

## Evidence
- **Symptom:** `python report.py` → `Total: 41`. The expected total from `data.csv` is 42.35.
- **Where it first goes wrong:** the rows returned by `parse.load()` are already `{'amount': 10}, {'amount': 20}, {'amount': 11}`. When I give `total()` the real values directly, it returns `42.35`, so the summing code is fine.
- **Proof in both directions:**
  - With the truncation in place, the unmodified code prints `Total: 41`.
  - With only `parse_amount` replaced by `Decimal(v)` (patched in memory, no file edited), `report.render()` → `Total: 42.35`.

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| `total()` adds wrong | Ran `total()` on the true values | 42.35 | Ruled out |
| Parsing loses value | Looked at the rows `load()` returns | 10, 20, 11 | Confirmed |
| The `int()` truncation is the whole cause | Swapped only `parse_amount` | 41 → 42.35 | **Proven** |

**Why the tests didn't catch it:** `test_totals.py` only tests `total()`, and only with whole numbers. Nothing tests `parse.py` or runs the full path with amounts that have cents.

## Proposed fix (not applied)
The diagnosis is done and I haven't changed any files. The fix is small, but it changes the output format (`41` → `42.35`) and how money is stored in the rows, so you should choose it:

```python
# parse.py
from decimal import Decimal

def parse_amount(value):
    return Decimal(value)   # exact cents; float would drift, int truncates
```

The other option is to store integer cents (`int(Decimal(value) * 100)`) and format them at display time. Either way, don't use `float`, because it adds rounding error to money.

**Regression test** (this is the minimal reproduction):
```python
# test_report.py
import unittest
from decimal import Decimal
from parse import parse_amount
from report import render

class Report(unittest.TestCase):
    def test_keeps_cents(self):
        self.assertEqual(parse_amount("10.50"), Decimal("10.50"))

    def test_fixture_total(self):
        self.assertEqual(render("data.csv"), "Total: 42.35")
```
Both tests fail on the current code and pass with the fix. I can apply it if you pick one of the two options.