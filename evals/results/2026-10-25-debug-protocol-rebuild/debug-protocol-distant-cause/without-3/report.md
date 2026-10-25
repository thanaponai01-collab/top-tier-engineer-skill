The bug is in the parsing step, at `fixture/parse.py:6`, not in the addition:

```python
def parse_amount(value):
    return int(float(value))
```

`int()` drops everything after the decimal point, so each amount loses its cents as soon as it's read from the CSV:

| id | CSV value | after parsing |
|----|-----------|---------------|
| 1  | 10.50     | 10            |
| 2  | 20.25     | 20            |
| 3  | 11.60     | 11            |

I ran `python report.py` and it printed `Total: 41`, matching the customer's report. Printing the parsed rows shows the amounts are already whole numbers before they're added. The correct total is **42.35**, so the statement is short by 1.35.

`totals.py` adds correctly; it just receives amounts that are already cut down. The tests didn't catch this because `test_totals.py` only checks `total()` with whole-number amounts and never tests `parse_amount`.

When you want it fixed, the amounts should be parsed as `decimal.Decimal` rather than `float` so the cents add up exactly. A test for `parse_amount` with a value like `"10.50"` would cover it. I haven't changed anything.