The problem is in parsing, not in adding up. `fixture/parse.py:6` cuts off the cents of every amount as it reads the file:

```python
def parse_amount(value):
    return int(float(value))
```

`int()` drops the decimal part instead of rounding it, so each row loses its cents before `total()` ever sees it. I loaded the rows to check:

| id | CSV value | Parsed value |
|----|-----------|--------------|
| 1  | 10.50     | 10           |
| 2  | 20.25     | 20           |
| 3  | 11.60     | 11           |

`10 + 20 + 11 = 41`, but the real total is **42.35**. The customer is short by $1.35, the sum of the three amounts' cents.

- **`totals.py` is correct.** It adds up whatever numbers it's given.
- **`report.py` is correct.** It only prints the result.
- **The tests didn't catch it** because `test_totals.py` only passes whole numbers straight to `total()`. Nothing tests `parse_amount` or uses decimal amounts.

When you want it fixed, a plain `float()` would get rid of the 41 but can show small rounding errors with money. `decimal.Decimal` (or storing amounts as integer cents) is the safer choice, along with a test that parses a value like `"10.50"`. I haven't changed anything.