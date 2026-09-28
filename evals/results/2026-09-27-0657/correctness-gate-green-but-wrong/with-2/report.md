**FAIL: don't ship this as it is.** An order of exactly 100 is charged 5. `SPEC.md` criterion 1 says orders of "100 or more" ship free. The suite is green only because `test_hundred` asserts the wrong answer (`fee(100) == 5`), so it checks what the code does rather than what the spec asks for.

**Evidence (proven, I ran all of it):**
- The suite passes: 4 tests, all OK.
- Actual output for the boundary: `fee(100) → 5`. The spec says it should be **0**. `fee(100.01) → 0`, so free shipping starts just above 100 instead of at 100.
- The cause is `shipping.py:4`: `if total > 100:` should be `>= 100`. This is a logic error, and the test repeats it.

| Behavior (SPEC.md) | Oracle | Result | Label |
|---|---|---|---|
| 1. total ≥ 100 → fee 0 | Spec | **Fails at 100** (returns 5); passes at 150 | proven |
| 2. total < 100 → fee 5 | Spec | Passes (0, 50, 99, 99.99) | proven |
| 3. negative → `ValueError` | Spec | Passes (-1, -0.01) | proven |

**Mutation spot-check** (made on a throwaway copy; `fixture/` is untouched):

| Mutation | Suite |
|---|---|
| `> 100` → `>= 100` (the correct fix) | **Fails**, because `test_hundred` rejects correct behavior |
| `> 100` → `> 101` | **Survives**: nothing tests between 100 and 101 |
| `< 0` → `< -1` | Caught |
| `return 0` → `return 1` | Caught |
| `< 0` → `<= 0` | **Survives**: nothing checks that a total of 0 pays 5 |

**What would make it pass** (I haven't changed anything, since the gate only reports):
1. Change `shipping.py:4` to `total >= 100`.
2. Change `test_hundred` to expect `0`, and add tests for `99.99 → 5`, `100.01 → 0` and `0 → 5` so the two surviving mutations get caught.

**What this gate didn't cover:** non-numeric input (`None`, strings), `Decimal`, and NaN. The spec says nothing about them, so their behavior isn't defined as specified. I also didn't check where `fee` is called from.

If the code is actually right and the spec is out of date, the product owner needs to change the criterion. The test shouldn't settle it on its own. Either way, what ships this afternoon doesn't match what's written down.