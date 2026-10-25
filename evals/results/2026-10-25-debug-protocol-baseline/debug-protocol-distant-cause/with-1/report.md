I found and proved the cause: `parse_amount` in `fixture/parse.py:6` throws away the cents. The total should be **42.35**, and `report.py` prints **41**. You asked for diagnosis only, so nothing in `fixture/` was changed.

**What goes wrong:** `return int(float(value))` cuts each amount down to a whole number (10.50 → 10, 20.25 → 20, 11.60 → 11). That loses 1.35 before the numbers are ever added. `totals.py` and `report.py` are both correct; the short total just becomes visible in the report.

**Why the tests didn't catch it:** `test_totals.py` only tests `total()`, and only with whole numbers. Nothing tests `parse.py`, so nothing ever checks decimal amounts from start to finish.

**Reproduce:** run `cd fixture && python report.py` with the shipped `data.csv`. It prints `Total: 41`.

**Where the wrong number first appears:**
| Step | Value |
|---|---|
| Raw CSV amounts | `10.50, 20.25, 11.60` (sum 42.35) |
| After `load()` | `[10, 20, 11]` ← first wrong |
| `total()` given the exact amounts | `42.35` (correct) |

**Proof in both directions** (run on a throwaway copy, with only `parse_amount` changed):
- Original code: `Total: 41`
- `parse_amount` changed to return `Decimal(value)`: `Total: 42.35`

**Ideas I checked:**
| Idea | Experiment | Result | Verdict |
|---|---|---|---|
| `total()` adds wrong | Ran `total()` on the exact amounts | 42.35 | Ruled out |
| `report.py` formats wrong | It only prints `total(load())`, and the value is already wrong by then | — | Ruled out |
| `parse_amount` truncates | Looked at `load()` output, then swapped only `parse_amount` | `[10,20,11]`; 41 becomes 42.35 | **Confirmed** |

**Proposed regression test** (not added):
```python
def test_report_keeps_cents(self):
    self.assertEqual(render("data.csv"), "Total: 42.35")
```

For a fix, I'd parse amounts as `Decimal` rather than `float`, so money values don't pick up rounding errors. I can make that change and add the test if you want.

`fixture/` is as it was: the experiments ran in a temporary copy that has been deleted, and I removed the `__pycache__` folder my runs created.