I found and fixed the bug: the checkout fee was 11 cents instead of the 10 that SPEC.md requires. I proved the cause both ways, recorded the failing check before the fix and the passing one after, and the final strict run passes. Nothing was committed, pushed or deployed (the folder isn't a git repo).

## Diagnosis

- **What went wrong:** `python checkout.py` printed `111`. SPEC.md says the checkout adds a fixed 10-cent fee, so it should print `110`. The existing test failed with `111 != 110`. The extra cent appeared at every price I tried (0, 1, 100, 999).
- **Cause:** `app.total` returned `cents + 11` instead of `cents + 10`. `checkout.py` just prints `total(100)`, so the wrong value comes straight from `app.py:2`.
- **Proof in both directions** (run in a scratch copy):

  | Condition | `checkout.py` prints | existing test |
  |---|---|---|
  | Original code (`+ 11`) | `111` | FAILED, `111 != 110` |
  | Only that number changed to `+ 10` | `110` | OK |

- **Why it wasn't caught:** `tests/test_total.py` did catch it and was failing. Nothing was set up to run it, since VERIFY.md had no checks. No test ran `checkout.py` itself.

| Hypothesis | Experiment | Result | Verdict |
|---|---|---|---|
| The extra cent depends on the price (rounding) | Ran `total` at 0, 1, 100, 999 | Always +11 | Ruled out |
| The fee number 11 is the cause | Changed only 11 to 10 in a scratch copy | Still printed `111` | Inconclusive (see next row) |
| The code being run isn't the code on disk | Checked which file Python loads, then reran with no cached bytecode | Cached bytecode from my first run was copied into the scratch copy. My edit kept the same file size and time, so Python used the old cached code. | Confirmed as a testing artifact |
| The fee number 11 is the cause (rerun cleanly) | Same one-number change, no cached bytecode | `111` becomes `110`, test fails then passes | **Proven** |

## Fix and regression evidence

- **Fix:** `app.py` now returns `cents + 10`.
- **New `tests/test_checkout.py`:**
  - One test runs `checkout.py` the way a user would and expects `110`. It uses `python -B` so stale cached bytecode can't fool it.
  - One test checks that the fee is exactly 10 cents and the result is whole cents, at prices 0, 1, 99, 100 and 12345.
- **VERIFY.md:** I added a "Checkout fee" section that runs `python -B -m unittest discover tests`, takes its expected values from SPEC.md, and records the failure it must catch. The existing note about the live payment gateway is kept unchanged.
- **Before the fix:** the check failed through the verify-loop helper with `expected checkout total 110, got 111`, and that failure is kept on record.
- **After the fix:**
  - The check passes and the strict run passes, including a rerun without cached results. Status is `VERIFY-STATE: green`.
  - The helper deliberately broke the code in temporary copies: a 9-cent fee and 4 automatic changes across `app.py` and `checkout.py`. The check caught all of them.
- **Kept evidence:** `fixture/.verify-state.json` and `fixture/.verify-state-cache/` hold the before and after results. The checked summary is at `%TEMP%\checkout-fee-answer.md`. The helper's own answer check accepted it.

## Coverage limits

- **Live payment gateway:** not tested. It's outside this project, as VERIFY.md already notes. Whether the gateway actually charges the corrected total still needs a manual or staging check.
- **Inputs:** the checks use fixed example prices. Negative, non-integer or very large amounts aren't covered, and SPEC.md doesn't say what should happen with them.
- **Checkout entry point:** only exercised with its hard-coded price of 100, because `checkout.py` takes no input.
- **Skill file missing:** debug-protocol says to follow verify-loop's `references/handoff.md`, but that file isn't in the installed skill. I followed its `verify-change.md` and format guide instead.