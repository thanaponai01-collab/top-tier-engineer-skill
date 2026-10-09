Local verification for `fixture/` is set up and green. The one covered behavior is the fixed 10-cent checkout fee at price 100.

**Files**
- **Created:** `BRIEF.md`, `BUILD.md`, `FEATURES.md` (marked partial), `verification/fee_mutation.json`, `.gitignore` (ignores `.verify-state.json`, `.verify-evidence/`, `__pycache__/`), and `.verify-state.json`.
- **Refreshed:**
  - `VERIFY.md` now has a "Checkout fee" section. The original MANUAL gateway blind spot is kept verbatim, with one added blind spot for untested inputs.
  - `AGENTS.md` has one start-here block appended. The original lines are untouched.
- **Unchanged:** `app.py`, `SPEC.md`, `tests/test_total.py`.

**Environment:** Python 3.11.9, stdlib `unittest`, working directory `fixture/`. No dependencies were needed.

**Executed**
- `python -m unittest discover tests` passed on the unchanged code.
- `verify.py challenge` with the mutation `cents + 10` → `cents + 11` was caught. The rejection signal was `AssertionError: 111 != 110 : expected total 110`, from a scratch copy, so `app.py` was not touched.
- `verify.py baseline`, then `run --strict` and `status` printed `VERIFY-STATE: green`.
- The second pass left setup files unchanged and source hashes identical. Strict and status were green again. `context_budget.py --check-handoff` first found 2 gaps because my links used markdown form. I changed them to plain `intent: BRIEF.md` and `work: BUILD.md`, and it now reports 0 gaps. That edit made status stale, so I re-ran strict and it is green again.

**Verdict:** local verified, strict green. Context is complete only for what `SPEC.md` and `AGENTS.md` state, so it is partial overall.

**Limits**
- Only one test at price 100 covers the 10-cent fee. Other prices, zero, negative and non-integer inputs have no requirement, so they are unverified.
- The live payment gateway is untested; it stays as the manual blind spot.
- Only one mutation was tried, so this doesn't show the check catches every fee mistake.
- I made no check edits and no product edits. There is no git repo here, so I didn't commit, and I set up no CI or deploy.

**Next step** (also in `BUILD.md`): get owner requirements for other inputs, then add a test and its own rejection proof for each.

The `claude.ai Notion` connector and the `plugin:design` servers (asana, atlassian, figma, intercom, linear, slack) need authorization before they work. That has to be done in your claude.ai connector settings or with `/mcp` in an interactive session. None of them were needed for this task.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: small Python checkout library. Source: SPEC.md, AGENTS.md.

## Requirements
- Checkout adds a fixed fee of 10 cents to the supplied price (SPEC.md).
- Amounts are integer cents (AGENTS.md, MANUAL).

## Open questions
- Owner intent beyond the above (rounding, negative/zero prices, other fees) is unknown; not derived from code.
- Live payment gateway is out of scope locally.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

Status: library exists (`app.py`); local verification set up in VERIFY.md.

## Next
Obtain owner requirements for inputs beyond price 100 (zero, large, invalid), then add checks.
Done when each new requirement has a test in tests/ and its own rejection proof in VERIFY.md.

## Blockers
- Requirements for other inputs are missing.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features (partial map)

| Behavior | Requirement | Entry point | Implementation | Check | Evidence |
|---|---|---|---|---|---|
| Checkout fee | SPEC.md: fixed 10-cent fee | `app.total(cents)` | app.py | tests/test_total.py via VERIFY.md "Checkout fee" | see VERIFY.md state |
