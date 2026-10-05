**Cause (proven):** `parse_amount` in `fixture/parse.py:5` returns `int(float(value))`, which truncates each amount to a whole number. The rows 10.50, 20.25 and 11.60 become 10, 20 and 11, so the total is 41. The real total is 42.35, so the statement is short by 1.35.

**Failure signature:** `python report.py` prints `Total: 41`, where `data.csv` sums to 42.35. The wrong value first appears in `parse.py`. `report.py` only shows it, and `totals.py` sums correctly what it is given.

**Proof in both directions.** I ran this as an in-memory probe and edited no files:
- **Cause present:** `Total: 41`.
- **Only the truncation removed** (`parse_amount` swapped for `Decimal(value)` in memory): `Total: 42.35`.

**Why it wasn't caught:** `test_totals.py` only tests `total()` with hand-made integer rows. Nothing tests parsing or the CSV → report path with fractional amounts.

| Hypothesis | Experiment | Verdict |
|---|---|---|
| `total()` sums wrongly | Read `totals.py`: it is a plain `sum` | Ruled out |
| CSV format (CRLF line endings) corrupts values | `cat -A data.csv`: `csv` with `newline=""` handles CRLF, and the values parse | Ruled out |
| `parse_amount` truncates the decimals | Swap in `Decimal`; the total becomes 42.35 | **Confirmed** |

**Regression test to add (not applied):** `render("data.csv")` should equal `"Total: 42.35"`. It currently returns `Total: 41`. Add a case with fractional amounts that must be kept. I haven't applied a fix because you asked for diagnosis only. The fix is to use `Decimal` (or integer cents) instead of `int(float())`. Money shouldn't be summed as floats, since the sum could print as something like 42.349999….