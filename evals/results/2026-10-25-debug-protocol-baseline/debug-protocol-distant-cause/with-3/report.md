## Debug-protocol report: the statement total is short

**The cause:** `parse_amount` in `fixture/parse.py:6` does `int(float(value))`. That cuts the cents off every amount as soon as the CSV is read. The rows add up to $42.35 but the report prints `Total: 41`, so the customer is short $1.35, which is the three rows' cents (0.50 + 0.25 + 0.60).

**Where it goes wrong:** the values are already wrong when `parse.load` returns them, which is earlier than where the problem shows up. `report.py` just displays them, and `totals.total` adds them up correctly.

**Why the tests didn't catch it:** `test_totals.py` only tests `total()`, and only with whole numbers (`10 + 20`). Nothing tests parsing or the report end to end, and no test uses an amount with cents. The tests pass while the output is wrong.

### Experiments
I ran these with a probe script in a scratch directory. The fixture files were never edited; a checksum check before and after confirms they're unchanged.

| # | Hypothesis / step | Experiment | Result | Verdict |
|---|---|---|---|---|
| E1 | Reproduce | `python report.py` in `fixture/` | `Total: 41` | Reproduced |
| E2 | Existing tests would catch it | `python -m unittest test_totals` | OK | They don't: they only use whole numbers |
| E3 | The input data is wrong | Read the raw CSV amounts and add them exactly | `['10.50','20.25','11.60']` → 42.35 | Ruled out: the data is fine |
| E4 | Parsing loses value | Look at what `parse.load()` returns | `[10, 20, 11]` | First point where the values are wrong |
| E5 | Adding up loses value | `totals.total` on exact Decimal rows | 42.35 | Ruled out: `total()` is correct |
| E6 | Truncation in `parse_amount` is the cause | Run `report.render()` with the code as is, then with only `parse_amount` replaced by `Decimal` | **With the cause:** `Total: 41` · **Without it:** `Total: 42.35` | **Proven both ways** |

### Proposed regression test (not added)
This goes through the real entry point:
```python
def test_report_keeps_cents(self):
    from report import render
    self.assertEqual(render("data.csv"), "Total: 42.35")   # currently: "Total: 41"
```
A unit test for the parsing step would also help: `parse_amount("10.50") == Decimal("10.50")`. Keep the existing `total()` tests so the whole-number cases are still covered.

**Suggested fix (not applied):** have `parse_amount` return `Decimal(value)`. Don't use `float`: adding floats can produce totals like `42.349999…`. Decide too how the report should format money, for example always two decimal places.

If you'd like me to apply the fix, I'll first record the regression test failing on the current code, then show it passing after the fix using verify-loop.