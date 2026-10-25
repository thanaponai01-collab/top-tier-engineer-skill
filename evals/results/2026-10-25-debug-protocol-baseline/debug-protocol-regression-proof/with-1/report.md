The checkout fee is fixed: `checkout.py` now prints **110** for a 100-cent price, as SPEC.md requires (a fixed 10-cent fee). The cause was the fee in `app.total` being 11 cents instead of 10 (`return cents + 11`). That made every total 1 cent too high (0→11, 100→111, 250→261), and the checkout entry point passed it straight through. Nothing was committed, pushed or deployed.

**Why it wasn't caught:** `tests/test_total.py` already failed on this bug (`111 != 110`), so the test existed but its result was ignored. There was also no check through `checkout.py`, and VERIFY.md listed no checks, so nothing ever ran it.

**Proof (both directions, on a scratch copy with Python's compiled-file cache off):**
```
cause present        -> 111
only fee 11 -> 10    -> 110
fee back to 11       -> 111
```

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| The total is wrong at every price, not just 100 | `total(0), total(100), total(250)` | 11, 111, 261 | Confirmed: a constant +1 offset |
| `checkout.py` loads a different `app` | printed `app.__file__`, checked PYTHONPATH | the local `fixture/app.py`, PYTHONPATH empty | Ruled out |
| Changing the fee to 10 fixes it (first try) | edit in scratch, run `checkout.py` | still printed 111 | My mistake, not the bug: Python reused a stale compiled copy of the old file, because the edit kept the same size and time stamp |
| Same experiment, cache off (`-B`) | the proof above | 111 / 110 / 111 | Cause proven |

**Changes in `fixture/`:**
- `app.py`: the fee is now `+ 10`.
- New `tests/test_checkout.py`:
  - runs the real `checkout.py` and expects `110`;
  - checks the fee stays exactly 10 cents for prices 0, 1, 100, 250 and 99999.

  Expected values come only from SPEC.md.
- `VERIFY.md`: added a `Checkout fee` section (the test command, SPEC.md as the reference, the failure message and how it was proven). The live-gateway blind spot is kept word for word.

**Regression evidence (recorded by verify-loop's `verify.py`):**
- **Before the fix:** red, 7 failures. Examples: `'111' != '110'` from `checkout.py`, `11 != 10` at price 0, `100010 != 100009` at price 99999, and the old test's `111 != 110`.
- **After the fix:** `ADVANCE: done`, with the full and strict runs both passing and the checks frozen.
- **Answer check:** a filled-in summary passed the tool's own check (`answer-check: ok`).
- **Where it's kept:** `fixture/.verify-state.json` and `.verify-state-cache/`, plus that summary in `answer.md` just outside `fixture/`.
- **To re-run:** `python -m unittest discover tests` from `fixture/`.

**Coverage limits:**
- The live payment gateway isn't exercised; it's outside this local project and still needs a manual check.
- SPEC.md says nothing about negative, non-integer or very large prices, so none of those are tested.
- `checkout.py` hardcodes a price of 100, so the entry-point check only covers that price. Other prices are tested only through `total()`.
- Green covers this one feature only.
- The debug skill points to `references/handoff.md`, which doesn't exist in the installed verify-loop. I followed verify-loop's main instructions instead.
- I didn't run a separate `challenge` step that plants deliberate errors in the code to see whether the checks catch them. The proof that the checks fail on a wrong product is the original bug itself.

<!-- file written by the agent: answer.md -->
VERDICT: green
Claim: checkout.py prints the supplied price plus a fixed 10-cent fee (110 for 100); expected values come from SPEC.md ("fixed fee of 10 cents").
Proven: Checkout fee went red on fee constant in app.total was 11 cents (shipped bug); checkout.py printed 111, the entry-point test went red with '111' != '110'; fixed to 10 (`python -B -m unittest discover tests`, signal: '111' != '110')
Passed: Checkout fee (`python -B -m unittest discover tests`)
GAP blind spot: MANUAL: live payment gateway is outside this local project. Not exercised here; it needs a manual or staging check by whoever owns the gateway integration.
Covers: the mapped features only; behavior no check exercises is not covered
