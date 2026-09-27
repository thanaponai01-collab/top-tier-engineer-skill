**The gate fails. Don't ship this afternoon as-is.** An order of exactly 100 is charged 5, but `SPEC.md` criterion 1 says "100 or more ships free". The suite is green only because `test_hundred` asserts the wrong value, so the test agrees with the bug instead of the spec.

**Cause: a logic error, with a test that locks it in.** `shipping.py:4` uses `total > 100` where the spec needs `>= 100`, and `test_shipping.py:14` asserts `fee(100) == 5`.

Real output from running `fee()` directly:
```
99    -> 5
100   -> 5   ← spec says 0
100.01 -> 0
```

| Behavior | Oracle | Result | Evidence |
|---|---|---|---|
| ≥100 ships free | Spec 1 | **Fails at 100** | proven |
| <100 pays 5 | Spec 2 | Passes (0, 50, 99, 99.99) | proven |
| Negative total → `ValueError` | Spec 3 | Passes at -1 | proven |

**Mutation check** (each break applied to a throwaway copy; `fixture/` was never modified):

| Mutation | Suite |
|---|---|
| `> 100` → `>= 100` (the spec-correct fix) | **Fails** at `test_hundred`: the suite rejects the correct code |
| flat fee 5 → 6 | caught |
| error branch dropped | caught |
| `> 100` → `> 101` | **survived** |
| `< 0` → `<= 0` (0 now rejected) | **survived** |
| `< 0` → `< -1` | **survived** |

My first mutation run reported M2 and M6 as caught. That harness was wrong; re-running with full output showed they survive, and the table uses the corrected results.

**Blind spots to close:** the suite doesn't test the free-shipping boundary correctly (99 vs 100) or the zero/negative boundary (0 and -1 as a pair).

**Not covered by the spec:** `fee(float('nan'))` returns 5, and non-numeric input raises `TypeError`. Neither is wrong per the spec, but whoever owns it should decide whether NaN should be rejected.

**Fix, for the spec owner to confirm:** change line 4 to `total >= 100` and `test_hundred` to expect 0. Then add tests for `fee(99) == 5` and `fee(0) == 5`. The gate only judges, so I haven't changed anything. Want me to make that change?