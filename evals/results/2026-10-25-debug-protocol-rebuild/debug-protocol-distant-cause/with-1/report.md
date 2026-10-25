The total goes wrong in `parse_amount` at `fixture/parse.py:6`. I haven't changed any code.

**What happens:** `python report.py` prints `Total: 41`. The amounts in `data.csv` are 10.50, 20.25 and 11.60, so it should print `Total: 42.35`.

**The cause:** line 6 is `return int(float(value))`. The `int()` throws away the cents on every amount before anything adds them up. That loses 0.50 + 0.25 + 0.60 = 1.35, which is exactly how short the statement is. `totals.py` and `report.py` are fine; they just add up and print numbers that are already wrong.

**How I checked it:**
- With the code as it is, `python report.py` prints `Total: 41`.
- With only that line changed to `return float(value)`, the same command prints `Total: 42.35`.

**Why the tests didn't catch it:** `python -m unittest discover` passes on the broken code. `test_totals.py` only gives `total()` whole numbers it made up (10 and 20, or an empty list). No test reads the CSV or calls `parse_amount`, so a decimal amount never goes through the parsing step.

**Test to add with the fix:** a test that checks `parse_amount("10.50") == 10.50`, or one that checks `render()` on the sample data gives `Total: 42.35`. It could go in `test_totals.py` or a new `test_parse.py`.

**Two things to decide when fixing:**
- `float` fixes this data, but floats can be slightly off for money, for example adding 0.1 + 0.2. Using `Decimal` would avoid that.
- I only tried this one `data.csv`. Other inputs, like negative amounts or blank values, weren't tested.

I deleted the `.debug/` working folder, since this was diagnosis only.