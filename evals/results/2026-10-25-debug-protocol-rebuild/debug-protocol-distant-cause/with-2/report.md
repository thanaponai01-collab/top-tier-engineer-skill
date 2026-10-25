The total goes wrong at `fixture/parse.py:6`. `parse_amount` does `int(float(value))`, which cuts the cents off every amount as the CSV is read. The data adds up to 10.50 + 20.25 + 11.60 = **42.35**, but the report adds 10 + 20 + 11 = **41**. The adding in `totals.py` and the printing in `report.py` are fine; they just get amounts that are already cut short.

**Proof, both ways:**
- As the code is now, `python report.py` prints `Total: 41`.
- With only that line changed to `return float(value)`, it prints `Total: 42.35`.

**Why the tests didn't catch it:** `python -m unittest discover` passes on the broken code. `test_totals.py` only passes whole numbers (`10`, `20`) straight into `total()`, so no test ever reads the CSV, calls `parse_amount`, or uses an amount with cents.

**Regression test to add when it gets fixed:** a test that runs `parse.load` (or `report.render`) on `data.csv` and expects 42.35, plus a direct check that `parse_amount("10.50") == 10.50`.

**What this didn't cover:** I only ran it on this three-row file. For the fix, `float` worked here, but `decimal.Decimal` is safer for money, since floats can give totals like 42.349999… on other data.

Nothing was changed: the code is as it was, and I deleted the `.debug/` working folder because this was diagnosis only.