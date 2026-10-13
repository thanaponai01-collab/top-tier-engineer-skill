## Verdict: FAIL. Don't ship this afternoon as-is.

**Why it fails:** `fee(100)` returns **5**, but SPEC.md criterion 1 says an order of "**100 or more** ships free". `shipping.py:4` uses `total > 100` where the spec needs `>= 100`. This is a logic error.

**Why the suite is green anyway:** `test_hundred` asserts `fee(100) == 5`. That test checks what the code does, not what the spec says, so it locks the bug in. When I mutated the code to the spec-correct `>= 100`, that test was the one that failed.

### Results

| Behavior | Oracle | Result | Evidence |
|---|---|---|---|
| Total ≥ 100 ships free (criterion 1) | Spec | **FAIL at 100** (gives 5, should be 0); passes at 100.01 and 150 | proven |
| Total < 100 pays 5 (criterion 2) | Spec | Pass at 0, 99, 99.99 | proven |
| Negative total raises `ValueError` (criterion 3) | Spec | Pass (`-1`) | proven |
| Existing suite | n/a | 4/4 green, but `test_hundred` contradicts the spec | proven |

**A real input and output:** `fee(100) → 5`; the spec expects `0`.

### Mutations
I ran these on a temp copy. `fixture/` was not modified.

| Mutation | Suite |
|---|---|
| `> 100` → `>= 100` (the spec-correct code) | Failed, but only because `test_hundred` is wrong |
| `< 0` → `<= 0` | Caught |
| `return 5` → `return 4` | Caught |
| Negative-total guard removed | Caught |
| `> 100` → `> 101` | **Survived**: nothing tests values between 100 and 101 |

### What the gate can't see
- No other callers or environments were checked. This only covers the module and its tests.
- The spec doesn't say how to handle non-numeric input, `NaN`, or money precision, so those are **untestable as specified**.

### Fix (the gate doesn't apply it)
1. Change `shipping.py:4` to `if total >= 100:`.
2. Rename `test_hundred` to something like `test_exactly_100_ships_free` and change it to assert `fee(100) == 0`.
3. Add a test that `fee(99.99) == 5` so the boundary is pinned from both sides. Together these also kill the surviving `> 101` mutation.

If the spec is what's wrong, and the business really means "over 100", then the owner needs to change SPEC.md. The test shouldn't quietly override it. Either way, the code and the spec disagree right now, so this shouldn't ship until one of them changes.