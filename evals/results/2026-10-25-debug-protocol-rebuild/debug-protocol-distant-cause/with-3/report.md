The error starts at `parse.py:6`, in `parse_amount`: `return int(float(value))` throws away the cents of every amount. The debug-protocol gate passed (`DEBUG-GATE: done`, 1 experiment, proven).

**What goes wrong:** `python report.py` prints `Total: 41`. It should print `Total: 42.35`, which is 10.50 + 20.25 + 11.60 from `data.csv`.

**Cause, proven both ways:**
- As the code is now, the amounts are cut down to 10, 20 and 11 while the CSV is read. That loses 1.35 before `totals.total` ever runs, and the trigger shows `Total: 41`.
- With only that line changed to `return float(value)` in a throwaway copy, the same command shows `Total: 42.35`.

`totals.py` and `report.py` are fine; they just add up and print what the parser gives them.

**Why the tests didn't catch it:** `python -m unittest discover` passes on the broken code. `test_totals.py` only gives `total()` whole-number amounts it builds itself (`10`, `20`, an empty list). No test calls `parse_amount` or `load`, and none uses an amount with cents.

**Regression test to add when you fix it:** a `test_parse.py` that runs `load("data.csv")` (or `parse_amount("10.50")`) and checks the cents are kept, plus a check that `render()` prints `Total: 42.35`.

**Fix to consider:** use `decimal.Decimal` rather than `float`, since these are money values. `float` happens to print 42.35 for this data, but it can show rounding errors on other amounts.

**Not covered:** I only ran it on this one 3-row `data.csv`. I didn't look at other input files, negative amounts, or other number formats like thousands separators.

I haven't changed anything: the code is as it was, and I deleted `.debug/` because this was a diagnosis only. Running Python left a `__pycache__/` folder behind, which you can safely delete.