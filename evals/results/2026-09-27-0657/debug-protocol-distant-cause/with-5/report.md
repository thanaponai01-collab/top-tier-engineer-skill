The customer is right. The statement should total **42.35**, not 41. `parse_amount` in `parse.py:6` calls `int(float(value))`, which drops the cents from every row: 10.50 becomes 10, 20.25 becomes 20 and 11.60 becomes 11. The customer loses 1.35 on this file, and the error grows with every row. I proved this by running it both ways (below).

## What's wrong

- **Symptom:** `python report.py` prints `Total: 41`. The expected total is 10.50 + 20.25 + 11.60 = 42.35.
- **Where it first goes wrong:** in parsing, not in adding up or printing. `load()` already returns `amount: 10`, `20`, `11`. `total()` gives the right answer, 42.35, when it gets the real values. `report.py` is only where the wrong number shows up.
- **Cause:** `parse_amount` turns each money string into a whole number, which throws away everything after the decimal point.
- **Why no test caught it:** `test_totals.py` only tests `total()`, and only with whole-number amounts. Nothing tests `parse.py`, and no test runs from the CSV through to the printed total. The existing tests pass.

## Proof, run both ways

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| `total()` adds wrongly | `total()` given 10.50, 20.25 and 11.60 directly | `42.35` | Ruled out |
| The parsed rows are already wrong | Printed the output of `load('data.csv')` | amounts `10, 20, 11` | Bad values first appear here |
| Removing the rounding fixes the total | `report.py` as is, then again with `parse_amount` swapped for `Decimal` in memory (no file edited) | `Total: 41` as is → `Total: 42.35` without the rounding | **Proven** in both directions |

## Suggested fix (not applied)

The fix is to parse amounts as exact decimals. I'd use `Decimal` rather than `float`, because floats pick up small rounding errors when you add money:

```python
# parse.py
from decimal import Decimal

def parse_amount(value):
    return Decimal(value)
```

The regression test is this reproduction, run from the CSV to the printed total. It fails today and should pass after the fix:

```python
# test_report.py
import unittest
from report import render

class Report(unittest.TestCase):
    def test_keeps_cents(self):
        self.assertEqual(render("data.csv"), "Total: 42.35")
```

One thing to check before applying it: the printed total will change from a whole number to something like `42.35`. If anything reads that output and expects a whole number, it will see the new format.

Want me to apply the fix and add the test?