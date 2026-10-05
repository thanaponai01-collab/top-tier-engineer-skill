**Cause (proven):** `parse_amount` in `fixture/parse.py:5` returns `int(float(value))`, which truncates the cents from every amount. The rows come out as 10, 20 and 11, so the total is 41 instead of 42.35. The wrong value first appears in `parse.py`. `report.py` is only where it gets noticed.

**Reproduction:** `cd fixture && python report.py` prints `Total: 41`. The CSV amounts are 10.50, 20.25 and 11.60, which sum to 42.35.

**Proof in both directions.** I ran these as one-off in-memory probes and edited no files.
- **Cause present:** `total(parse.load('data.csv'))` gives `41`.
- **Only the cause removed:** with `parse_amount` swapped for `Decimal(value)` and nothing else changed, the same call gives `42.35`, matching the raw sum.

| Hypothesis | Experiment | Verdict |
|---|---|---|
| `total()` drops or miscounts rows | Read the code; the sum is over all rows, and the probe with the parse fix gives the right total | Ruled out |
| `parse_amount` truncates the amounts | Swap in `Decimal` and rerun | **Confirmed** |

**Why it wasn't caught:** `test_totals.py` only feeds `total()` hand-built integer rows. Nothing runs the CSV through `load`, so the truncation is never exercised.

**Regression test to add (not yet written):** call `render("data.csv")` on that CSV and expect `Total: 42.35`. It fails today with `Total: 41`. I would use `Decimal` for the fix, since floats would print noise like `42.349999…`.

I haven't changed any code. Say if you want me to write the failing test and apply the fix.