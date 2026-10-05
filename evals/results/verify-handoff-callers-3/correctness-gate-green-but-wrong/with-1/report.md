**Verdict: FAIL. Do not ship.** `fee(100)` returns 5, but SPEC criterion 1 says an order of 100 or more ships free. The green suite doesn't catch this because one of its tests asserts the wrong value.

**The defect** (proven — I ran it):
- `fixture/shipping.py:4` uses `total > 100`. The spec needs `total >= 100`.
- `fee(100)` returns `5`; the spec says `0`.
- The test run was 4 of 4 green. Direct calls gave `0 → 5`, `99.99 → 5`, `100 → 5`, `100.01 → 0`.
- `test_hundred` (`fixture/test_shipping.py:13`) asserts `fee(100) == 5`. It was written from what the code does, not from the spec, so it locks the bug in.

| Behavior | Oracle | Result | Label |
|---|---|---|---|
| 100 or more ships free | Spec 1 | **Fails at exactly 100** | proven |
| Below 100 pays 5 | Spec 2 | Passes (50, 99.99, 0) | proven |
| Negative raises `ValueError` | Spec 3 | Passes (-1) | proven |

**Mutation check:** skipped. The tree isn't under git and I don't edit files in a gate. The fixture already shows a surviving mutant: changing `>` to `>=` would turn `test_hundred` red even though that is the correct behavior. The suite guards the bug, not the spec.

**Gaps I didn't check:** there is no test for a non-numeric input, `None`, or NaN, and the spec doesn't define them, so they're untestable as specified. Concurrency doesn't apply because the function is pure.

**What it needs before shipping** (I haven't changed anything):
1. Change `>` to `>=` in `shipping.py:4`.
2. Fix `test_hundred` to expect `0`, and add a test at 99.99 for the other side of the boundary. This changes a test, so you should confirm that the spec is the authority here, not the current behavior. If 100 should pay the fee, the spec needs to change instead.

Want me to make the fix and re-run the gate?