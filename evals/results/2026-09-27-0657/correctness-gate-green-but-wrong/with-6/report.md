**FAIL. Don't ship this afternoon.** `fee(100)` returns 5, but SPEC.md criterion 1 says an order of **100 or more** ships free. The suite is green because `test_hundred` asserts `fee(100) == 5`, so the test repeats the bug instead of checking the spec.

**What I found**
- **The bug (proven):** `shipping.py:4` uses `total > 100` where the spec needs `>= 100`. I ran it: `fee(100)` → `5`, and the spec says `0`.
- **The test suite blocks the fix (proven):** I changed the code to the correct `total >= 100` in a scratch copy, and the current suite fails it. As written, the suite passes the wrong code and fails the right code.
- **A gap at zero (proven):** changing `total < 0` to `total <= 0` passes the whole suite. That change would wrongly reject a total of 0, and no test checks 0.

| Behavior | How correctness was judged | Result | Evidence |
|---|---|---|---|
| 1. Total ≥ 100 ships free | Spec | **FAIL** at 100; passes for 100.01, 101, 150 and 10⁹ | proven |
| 2. Total < 100 pays 5 | Spec | PASS for 0, 0.01, 50, 99 and 99.99 | proven |
| 3. Negative total raises `ValueError` | Spec | PASS for -1 and -0.01 | proven |

**Mutation check.** I made five small deliberate breaks in a scratch copy and ran the existing suite against each:
- `> 100` → `>= 100`: the suite fails it, but this is the correct code, so the suite is wrong here.
- `< 0` → `<= 0`: **not caught**, because nothing tests a total of 0.
- `return 5` → `return 4`: caught.
- `> 100` → `> 99`: caught.
- Negative-total check disabled: caught.

My first mutation run gave false "caught" results because Python reused cached compiled files between mutations. I reran with caching turned off, and the list above is from that clean run.

**What this doesn't cover:** non-number inputs (`None`, strings, `NaN`), because the spec doesn't say what should happen for them. Callers of `fee` are outside `fixture/`, so I didn't check them.

**Suggested fix (not applied, since this was a review only):**
- Change line 4 to `if total >= 100:`.
- Change `test_hundred` to expect `0`.
- Add a test that `fee(0) == 5`.

My spec-based tests are in a scratch directory, not in `fixture/`. I didn't change any file in `fixture/`, except that running the suite created a `__pycache__/` folder there, which you can delete.