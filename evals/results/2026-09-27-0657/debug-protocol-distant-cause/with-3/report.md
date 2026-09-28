**The cause is `parse_amount` in `parse.py:6`. It does `int(float(value))`, which cuts off the cents from every row before anything gets added up.** The customer is short $1.35: the statement shows 41 when it should show 42.35. I've proven this by running it both ways. I haven't changed any files.

## Failure signature
- `python report.py` prints `Total: 41`.
- `data.csv` has 10.50 + 20.25 + 11.60, which is **42.35**.

## Where it first goes wrong
- **Parsing (bad):** `load("data.csv")` already returns amounts of `10, 20, 11`. The wrong value appears here.
- **Adding up (fine):** `totals.total` gives 42.35 when it gets the real decimal amounts.
- **Printing (fine):** `report.py` only prints what it's given. This is where the problem gets noticed, but it isn't the cause.

## Proof, both ways (*proven*)
I swapped out `parse_amount` in memory for the test and changed only that one thing:

| Run | Output |
|---|---|
| Cause present (code as shipped) | `Total: 41` |
| Cause removed (`parse_amount = Decimal(v)`) | `Total: 42.35` |

## Why no test caught it
`test_totals.py` only feeds whole numbers (`10`, `20`) into `total()`. The tests pass (`OK`), but they never exercise `parse.py` and never use a fractional amount. The bug sits between the tests and the real data.

## What I checked
| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| Parsing drops the cents | Print what `load()` returns | `10, 20, 11` | **Confirmed** |
| `total()` adds wrong | Call `total()` on the real decimals | 42.35 | Ruled out |
| Removing the `int()` truncation fixes the total | Replace `parse_amount` in memory, run `render()` | 42.35 | **Confirmed (cause removed)** |

## Suggested fix (not applied)
The fix belongs in `parse.py`, where the value first goes wrong, not in the report. It should use `Decimal` rather than `float` so money adds up exactly:

```python
from decimal import Decimal

def parse_amount(value):
    return Decimal(value)
```

Regression test, written from the minimal reproduction:

```python
def test_total_keeps_cents(self):
    from decimal import Decimal
    from parse import parse_amount
    rows = [{"amount": parse_amount(v)} for v in ("10.50", "20.25", "11.60")]
    self.assertEqual(total(rows), Decimal("42.35"))
```

After the fix the report would print `Total: 42.35`. If something reads this output and expects a whole number, check it before shipping. Should I apply the fix and add the test?