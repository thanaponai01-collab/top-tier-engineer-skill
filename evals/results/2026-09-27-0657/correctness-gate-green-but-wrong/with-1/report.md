**Verdict: FAIL. Don't ship this afternoon.** An order of exactly 100 is charged 5, but SPEC.md criterion 1 says it should ship free. The suite is green only because `test_hundred` checks for the wrong answer (`fee(100) == 5`). It locks the bug in instead of catching it.

**Why it fails:** a logic error, plus a test that contradicts the spec.
- `fixture/shipping.py:4` uses `total > 100` where the spec says "100 or more", which needs `>=`.
- `fixture/test_shipping.py:19-20`: `test_hundred` asserts 5. The spec says 0.

**Spec check (proven: I called `fee` directly and compared it to SPEC.md):**

| Behavior | Oracle | Input → output | Expected | Result |
|---|---|---|---|---|
| ≥100 ships free | Spec 1 | `fee(100)` → 5, `fee(100.0)` → 5 | 0 | **FAIL** (proven) |
| ≥100 ships free | Spec 1 | `fee(100.01)` → 0, `fee(150)` → 0 | 0 | pass (proven) |
| <100 pays 5 | Spec 2 | `fee(0)`, `fee(50)`, `fee(99.99)` → 5 | 5 | pass (proven) |
| Negative rejected | Spec 3 | `fee(-1)`, `fee(-0.01)` → ValueError | ValueError | pass (proven) |

**Mutation check (proven: each break was made in a throwaway copy, so `fixture/` was never touched):**

| Deliberate break | Suite result |
|---|---|
| `> 100` → `>= 100` (this is the correct code) | **Fails**, because `test_hundred` rejects the correct behavior |
| `< 0` → `<= 0` (a total of 0 is rejected) | **Not caught.** No test uses a total of 0 |
| `< 0` → `< -1` | Caught |
| fee 5 → 4 | Caught |
| threshold 100 → 101 | **Not caught.** Nothing tests between 100 and 101 |

My first mutation run reported every break as caught. That result was wrong: leftover compiled files meant the original code was being tested each time. I cleared them and reran; the table above is from the clean run.

**What it would take to pass** (I haven't changed anything):
1. In `shipping.py:4`, change `>` to `>=`.
2. Change `test_hundred` to expect 0, and name it for the bug, e.g. `test_exactly_100_ships_free`.
3. Add tests for a total of 0 (should be 5) and 99.99 (should be 5) to close the two gaps the mutations found.

**Out of scope:** the spec doesn't say what should happen with non-numeric input, NaN, or float rounding right at 100. That behavior can't be tested until someone decides what it should be. There's no git history here, so I couldn't check whether `test_hundred` was written on purpose.

Want me to make those three changes and rerun the gate?