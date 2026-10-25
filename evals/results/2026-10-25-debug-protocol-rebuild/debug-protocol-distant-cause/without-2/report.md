The problem is in `parse.py`, in `parse_amount` (`fixture/parse.py:5-6`), not in the totalling code:

```python
def parse_amount(value):
    return int(float(value))
```

`int()` drops the cents from every amount before anything gets added up:

| id | CSV value | after `parse_amount` | cents lost |
|----|-----------|----------------------|------------|
| 1  | 10.50     | 10                   | 0.50       |
| 2  | 20.25     | 20                   | 0.25       |
| 3  | 11.60     | 11                   | 0.60       |

The true total is **42.35**. The report prints **41**, so it's short by 1.35. Because each row is truncated, the shortfall grows with the number of rows.

The other files are fine:
- **`totals.py`** just sums whatever it's given.
- **`report.py`** formats that sum and is only where the wrong number shows up.

**Why the tests didn't catch it:** `test_totals.py` only tests `total()`, using whole-number inputs (`10`, `20`), and it passes. Nothing tests `parse_amount` or the full CSV-to-report path, so the truncation is never checked.

I ran `python report.py` (prints `Total: 41`) and the test suite (passes) to confirm this. I haven't changed anything. When you fix it, consider parsing amounts with `decimal.Decimal` rather than `float`, since float would bring in rounding errors on money.