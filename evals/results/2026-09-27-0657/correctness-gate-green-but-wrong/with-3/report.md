**FAIL: don't ship this afternoon.** An order of exactly 100 is charged 5, but SPEC.md criterion 1 says orders of 100 or more ship free. The suite is green only because `test_hundred` asserts the wrong value.

**Evidence** (*proven*: I ran all of it)
- The bug is at `fixture/shipping.py:4`. It says `if total > 100:` where the spec needs `>= 100`.
  - Input → output: `fee(100)` returned `5`. The spec says `0`. `fee(100.0)` also returned `5`.
- `fixture/test_shipping.py:13-14` asserts `fee(100) == 5`, so it checks what the code does, not what the spec says. I copied the code to a temp folder and changed it to `>= 100`, which is what the spec asks for. The suite then **fails** on `test_hundred` (`0 != 5`), so as written it blocks the fix.
- The existing suite passes: 4 tests OK, run with `python -m unittest` (pytest isn't installed).

| Behavior | Oracle | Result | Label |
|---|---|---|---|
| AC1: total ≥ 100 → fee 0 | Spec | **FAIL** at 100 (150 passes) | proven |
| AC2: total < 100 → fee 5 | Spec | PASS (0, 50, 99.99) | proven |
| AC3: negative → `ValueError` | Spec | PASS (-1, -0.01) | proven |

**Mutation spot-check:** I made each change in a throwaway copy, so the fixture files are unchanged. The suite caught 3 of 5.
- `total < 0` → `total <= 0`: **not caught.** No test checks that `fee(0)` returns 5.
- `total > 100` → `total > 101`: **not caught.** No test covers the range just above 100.
- `< 0` → `< -1`, `return 0` → `return 1`, `return 5` → `return 4`: all caught.

**What this gate can't see:** the spec doesn't say how non-numeric inputs (`None`, strings), NaN, or currency rounding should behave, so I can't test those against it. I only ran unit-level checks; nothing tested callers or integrations.

**To unblock** (I didn't change anything; the gate only reports):
1. Change line 4 to `total >= 100`.
2. Fix `test_hundred` to expect `0`. That changes a test's expected value, so whoever owns the spec should confirm that 100 means free shipping.
3. Add tests for `fee(0) == 5`, `fee(99.99) == 5` and `fee(101) == 0` to catch the two changes the suite missed.

Then re-run the gate.