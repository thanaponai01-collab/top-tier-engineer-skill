**Cause (proven):** `parse_amount` in `fixture/parse.py:6` does `int(float(value))`, which truncates the cents from every row. The amounts 10.50, 20.25 and 11.60 become 10, 20 and 11, so the total is 41 instead of 42.35.

**Two-direction proof.** I ran both in memory and edited no files.
- **Cause present:** `report.render()` gives `Total: 41`.
- **Only `parse_amount` replaced:** with a float-preserving version (rounded to 2 places), the same `data.csv` gives `Total: 42.35`. That matches an independent `Decimal` sum of the raw CSV values, 42.35.

**Where it first goes wrong:** `load()` returns `{'amount': 10}` for the first row, where the CSV says `10.50`. `totals.py` just sums what it is given, and `report.py` is only where the bad number shows up.

**Why it wasn't caught:** `test_totals.py` only feeds `total()` whole-number rows, and nothing tests `parse`. The parse-to-total path with fractional amounts has no test.

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| CSV data is bad (CRLF, odd values) | Read raw with `cat -A` and `csv.DictReader` | Values are clean: `10.50`, `20.25`, `11.60` | Ruled out |
| `total()` drops rows | Read the code and `load()` output (3 rows, none missing) | Sums all rows correctly | Ruled out |
| `parse_amount` truncates | Replace only that function | 42.35 | **Confirmed** |

**Regression test to add (not written):** `load("data.csv")` followed by `total(...)` must equal 42.35. It fails now with 41. For exact money values, `Decimal` or integer cents is safer than float. That choice is yours, so I haven't picked a fix.

I made no changes to the fixture, as this was diagnosis only. Want me to apply the fix and add the regression test?