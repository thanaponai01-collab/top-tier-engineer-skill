The bug is in `fixture/parse.py:6`. `parse_amount` throws away the cents:

```python
def parse_amount(value):
    return int(float(value))
```

`int()` cuts off everything after the decimal point, so each amount loses its cents as soon as the CSV is read:

| id | CSV | parsed |
|----|-----|--------|
| 1 | 10.50 | 10 |
| 2 | 20.25 | 20 |
| 3 | 11.60 | 11 |

The correct total is **42.35**. The report shows **41**, so the customer is short $1.35. I confirmed this by running `report.py` and printing what `load()` returns.

The other files are fine:
- `totals.py` just adds up what it's given, and that part works.
- `report.py` only prints the result.

The tests didn't catch this because `test_totals.py` only feeds whole numbers to `total()`. Nothing tests `parse_amount` or decimal amounts.

When you fix it, parse the amounts with `decimal.Decimal` instead of `float`, so money adds up exactly. I haven't changed anything.