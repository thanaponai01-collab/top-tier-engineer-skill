The problem is in `fixture/parse.py:6`, not in the totals code or the report:

```python
def parse_amount(value):
    return int(float(value))
```

`int()` cuts off the decimal part of every amount as it's read in, so the cents are gone before anything is added up. I ran the loader to confirm:

| id | CSV value | parsed value |
|----|-----------|--------------|
| 1  | 10.50     | 10           |
| 2  | 20.25     | 20           |
| 3  | 11.60     | 11           |

`totals.total()` adds those correctly to 41. The real total is **42.35**, so the statement is short by $1.35. Each row loses its fractional part, so the shortfall grows with the number of rows, and the result is always rounded down.

**Why the tests didn't catch it:** `test_totals.py` only tests `total()`, and only with whole numbers. Nothing tests `parse.py`, and no test uses decimal amounts.

**Note for the fix:** just removing `int()` and using `float` would bring back floating-point rounding errors. For money, `decimal.Decimal` (or whole cents as integers) is the usual choice. I haven't changed anything, as you asked.