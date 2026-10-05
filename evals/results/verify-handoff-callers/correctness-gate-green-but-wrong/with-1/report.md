**Verdict: FAIL. Don't ship.** `fee(100)` returns 5, but SPEC criterion 1 says an order of 100 or more ships free. The green suite doesn't catch it, because one test asserts the wrong value.

**Cause (proven, ran it):** `fixture/shipping.py:4` has `if total > 100`. It should be `>= 100`. I ran `fee()` on the boundary inputs:

| total | spec says | actual |
|---|---|---|
| 99.99 | 5 | 5 |
| **100** | **0** | **5** ✗ |
| 100.01 | 0 | 0 |

**Why the suite is green:** `test_hundred` (`fixture/test_shipping.py:13-14`) asserts `fee(100) == 5`. That describes what the code does, not what the spec requires. The suite agrees with the bug, so it can't detect it.

| Behavior | Oracle | Result | Evidence |
|---|---|---|---|
| ≥100 ships free | Spec 1 | **Fail at 100** | proven |
| <100 pays 5 | Spec 2 | Pass (50, 99.99) | proven |
| Negative raises `ValueError` | Spec 3 | Pass (-1) | proven |

**Not checked:**
- I skipped the mutation spot-check. The directory isn't a git repo, so I couldn't revert safely, and the boundary failure already shows the suite has a blind spot.
- I didn't test non-numeric input, `None`, NaN or float edge cases. The spec doesn't cover them, so they're untestable as specified.

**To fix, which needs your sign-off because it touches the test, so I haven't changed anything:**
1. In `shipping.py:4`, change `>` to `>=`.
2. In `test_shipping.py`, change `test_hundred` to expect `0`. That's correcting the test to match the spec, not weakening it. Also add a check at 99.99 so the other side of the boundary stays covered.

If the product really wants "over 100", then the spec is wrong rather than the code. Say so and I'll gate against the new criterion.