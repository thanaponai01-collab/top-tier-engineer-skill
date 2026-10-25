The problem is in `fixture/parse.py:6`, in `parse_amount`, when the CSV is read. The adding and printing steps are fine.

```python
def parse_amount(value):
    return int(float(value))
```

`int()` throws away the cents on every row. I ran the loader and these are the values it actually produces:

| id | CSV value | parsed |
|----|-----------|--------|
| 1  | 10.50     | 10     |
| 2  | 20.25     | 20     |
| 3  | 11.60     | 11     |

`totals.total()` adds those correctly to 41, and `report.py` prints that. The real total is **42.35**, so the statement is short by 1.35. Every row with cents is cut down, never rounded up, so the total can only come out low, which matches the customer's complaint.

The tests pass because `test_totals.py` only tests `total()` with whole numbers (`10`, `20`). Nothing tests `parse_amount` or uses a decimal amount, so the lost cents never show up in a test.

As you asked, I haven't changed anything. When you fix it, keep the cents with `decimal.Decimal(value)` rather than `float`, which can introduce rounding errors with money. Also add a parsing test that uses a value like `"10.50"`.