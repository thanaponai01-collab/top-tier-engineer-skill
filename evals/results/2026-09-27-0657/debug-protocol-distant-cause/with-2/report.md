The total comes up short because `parse_amount` in `fixture/parse.py:6` does `int(float(value))`, which drops the cents from every row. `totals.py` and `report.py` are fine; they just add up and print numbers that are already wrong. I tested this both ways and it holds.

**What fails:** `python report.py` prints `Total: 41`. The rows in `data.csv` add up to 10.50 + 20.25 + 11.60 = **42.35**, so the customer is short 1.35.

**Where it first goes wrong:** right after parsing. `load()` returns amounts `10, 20, 11` instead of `10.50, 20.25, 11.60`. Every row loses its cents before anything adds them up.

**Test in both directions:**
```
cause present (as shipped):              Total: 41
only the truncation removed (patched in memory, no file edited):  Total: 42.35
```

**Why the tests didn't catch it:** `test_totals.py` only feeds `total()` whole numbers it builds itself. Nothing tests `parse_amount` or runs from the CSV to the printed total, so the parser was never checked.

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| `total()` sums wrong | `total()` on the raw decimal amounts | 42.35 | ruled out |
| Parsing loses value | print `load('data.csv')` | amounts 10, 20, 11 | first wrong value |
| `int()` truncation is the cause | swap only `parse_amount` for `Decimal(v)` in memory | 41 → 42.35 | **proven** |

**Minimal reproduction, as a future regression test:**
```python
def test_parse_keeps_cents(self):
    from parse import parse_amount
    self.assertEqual(parse_amount("10.50"), Decimal("10.50"))

def test_report_total_matches_csv(self):
    from report import render
    self.assertEqual(render("data.csv"), "Total: 42.35")
```

**Suggested fix (not applied, since this was a diagnosis):** in `parse.py`, change the body of `parse_amount` to `return Decimal(value)` and add `from decimal import Decimal`. Use `Decimal` rather than `float` so money totals don't pick up rounding errors. If you'd rather store integer cents, that works too, but then `report.py` has to format the output. Tell me which you want and I'll apply it with the tests.