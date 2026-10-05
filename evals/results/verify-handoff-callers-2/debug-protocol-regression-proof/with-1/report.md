The checkout fee is fixed. The bug was the fee constant in `app.py:2`: it added 11 cents where SPEC.md says 10, so `checkout.py` printed 111 for a 100-cent price. It now prints 110.

**Proof of the cause (traced, and proven in both directions)**
- **Cause present:** `python checkout.py` printed `111`, and the existing `test_total.py` failed with `111 != 110`.
- **Cause removed:** changing only `11` to `10` made the same entry point print `110`. The fixed-fee test cases (`total(0)` is 10 and `total(1000)` is 1010) also pass.
- **Why it wasn't caught:** `VERIFY.md` mapped no checks. The one existing unit test was red and nothing ran it.

**Experiments**

| Hypothesis | Experiment | Result |
|---|---|---|
| The entry point has the wrong total | Ran `checkout.py` | Printed 111, so confirmed |
| `checkout.py` is correct and `total()` is off | Read `checkout.py`, which only calls `total(100)` | Ruled out, it adds no fee itself |
| The fee constant in `app.py` is the cause | Changed 11 to 10 with nothing else touched | Prints 110 and all checks pass, so confirmed |

**Changes**
- `app.py`: `+ 11` is now `+ 10`.
- Added `tests/test_checkout_entry.py`, which runs `checkout.py` as a subprocess and expects 110. It also checks the fee at prices 0 and 1000 so a percentage-style fee would fail. All expectations come from SPEC.md.
- `VERIFY.md` now has a "Checkout fee" section with the literal `fail-signal`, the oracle and the fail-proof note. The live-gateway blind spot is kept.

**Retained evidence**
- The rejection is in `fixture/.verify-state.json`: the check failed on `'111' != '110'` with the signal `expected checkout total 110, got 111`.
- After the fix, `verify.py run --strict` passed 2 of 2 checks and `status` printed `VERIFY-STATE: green`.
- The check files are frozen with `baseline`.
- `verify.py tests --strict` mapped all 3 tests to the feature, with none unmapped and none unable to fail.

**Coverage limits**
- The live payment gateway is not covered; it stays a MANUAL blind spot.
- Only integer-cent prices are checked, matching AGENTS.md.
- Negative prices and non-integer input aren't covered, because SPEC.md doesn't define them.
- There is no `## Run` section because this is a CLI script with no server to start. The helper prints a note about that, and it is harmless.
- Strict green covers only the mapped checkout-fee claim, not the whole app.
- The scratch-copy `challenge` mutation was not run; the retained rejection came from the original bug itself.

No commit, push or deploy happened, and this directory isn't a git repo anyway.