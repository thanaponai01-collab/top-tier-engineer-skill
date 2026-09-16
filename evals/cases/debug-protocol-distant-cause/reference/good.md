# Debug Protocol — fixture/

**Cause, proven: `parse.py:6` casts every amount with `int(float(value))`, so
the cents are discarded at load time, before anything is summed.**

Signature: `python report.py` prints `Total: 41`; `data.csv` sums to 42.35.

Reproduced on demand, three rows, no state involved. Localised by place: printed
the rows between the two layers — `load()` already returns `[10, 20, 11]`, so the
bad value first appears inside `parse.py`, not in `totals.py` or `report.py`.
Those two only carry a number that was already wrong.

Proven in both directions:
- with the cause present: `load("data.csv")` -> amounts `[10, 20, 11]`, total 41
- with only `parse_amount` returning `float(value)`: amounts `[10.5, 20.25, 11.6]`,
  total 42.35, and the same trigger no longer fails. Reverted after measuring.

| hypothesis | experiment | result | verdict |
|---|---|---|---|
| `sum()` in `totals.py` loses precision | summed the floats directly | 42.35, correct | rejected |
| `report.py` formats away the decimal | printed `repr(total(...))` | `41`, an int already | rejected |
| `parse_amount` truncates | printed `load()` output | `[10, 20, 11]` | confirmed |

Not caught because `test_totals.py` passes whole-number dicts straight to
`total()` and never runs `parse.py` at all, so no test exercises the conversion.

Regression test: `load()` on a row of `10.50` must return `10.5`.
