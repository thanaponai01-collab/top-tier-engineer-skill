---
name: verify-loop
description: Build the check before the work, then loop on it until it passes, so an agent can tell for itself whether it succeeded. Use at the start of any task with no way to tell it worked, when "done" was claimed without a run, when the human is the only one checking, or to map every feature to the tests that prove it (VERIFY.md).
---

# Verify Loop

Output is only as good as the check that judges it. An agent with a good check keeps going until it
passes, and the human stops being the bottleneck. An agent with no check, or a weak one, stops when
it feels done. So build the check first, make it hard to fool, and keep it in the repo where the next
session finds it.

## What makes a check good

1. **It can fail.** Run it against the broken or old state and see it go red before you trust a
   green. A check that has never failed proves nothing.
2. **It watches the real thing.** Run the program, hit the endpoint, open the page, read the output.
   Reading the code is not a check.
3. **It does not come from the work.** The check is written from the claim, not from the
   implementation, and the agent that did the work does not edit it to pass. For judgment calls
   (writing, design), write the rubric first and have a fresh context grade against it.
4. **Its failure is specific.** "expected 42, got 41 at step 3" says what to fix. "looks off" does not.
5. **It is cheap to rerun.** One command, seconds to a minute. A check too costly to run is a check
   that gets skipped.

*Test:* for each check, you can say what output it printed when you made it fail.

## The loop

1. **Name the claim.** What must be true when this is done, in terms you can observe. "Refunds work"
   is a wish; "POST /refund on a paid order returns 200 and the balance drops by the amount" is a claim.
2. **Choose the strongest check you can afford.** Weakest to strongest: types and lint, unit tests,
   integration tests, a real run of the built thing, a run on real data. Take the top rung this
   environment can execute, and add one below it for a fast signal.
3. **Record it in VERIFY.md** (format below). If tests already exist, `python <this skill's base
   directory>/scripts/verify.py init` drafts the feature map from them. Then finish the draft: read
   the code behind each test file and regroup by real feature (one feature can span several test
   files, one file can cover several features); give every feature a check that runs the built thing,
   not only a test; replace each TODO, and list the blind spots you can name. The draft is a
   starting point, and a VERIFY.md with TODOs left in it does not count as done.
4. **Prove it can fail.** Break the feature on purpose, watch a check go red, revert, and write one
   line under fail-proof saying what you broke. Do this before the work, or on the working state.
5. **Do the work in slices, and run `verify.py run` after each.** Read the failure text and fix that.
6. **Stop guessing.** Two failures on the same idea means your picture of the system is wrong: re-read
   the code and the failure before a third try. Give the loop a budget (about five rounds per
   feature); at the budget, stop and report what passes, what fails and what you would try next.
7. **Before you say done, check the check.** Look at what changed in VERIFY.md and the test files:
   no assertion loosened, no test skipped or deleted, no output hardcoded to match. A pass you got by
   editing the check is not a pass.

*Test:* the check was written before the change it judges, and you can name a moment it was red.

## VERIFY.md

At the repo root. One `##` section per feature; each bullet is `kind: command`, and a check passes
when its command exits 0.

```
## Refunds
- test: `python -m pytest tests/test_refunds.py -q`
- run: `python scripts/smoke_refund.py`
- fail-proof: changed the refund sign, test_refunds went red, reverted

## Blind spots
- the payment gateway is stubbed; real card declines are not exercised
```

`verify.py run` prints a result per feature, then what a green run does **not** cover: features with
no check (UNVERIFIED), checks nobody proved can fail, test files no feature names (orphans), and the
blind spots. `--strict` makes the unverified and unproven ones fail the run; use it for "done". A
bare `pytest` in a command attributes no file to a feature, so those files show as orphans; name the
files or their folder.

Commands run through the shell like a Makefile: run a VERIFY.md only from a repo you trust. Without
Python, run the same commands by hand and keep the same table.

## Checks by kind of work

| Work | Check |
|---|---|
| Code | tests, plus one real run of the built thing |
| UI | drive it in a browser, screenshot, compare to the spec |
| Data or migration | invariants (row counts, totals, no nulls where none allowed) and a sample checked against the source |
| Writing or research | rubric written first, each claim checked against its source by a fresh context |
| Config or infra | dry-run or plan diff, then the smallest real apply |

## Report

Verdict first: which features are verified, which failed, which are unverified. Paste the `VERIFY:`
summary line, list the blind spots, and say what you broke to prove each check can fail. Never
report a green run without its unverified and unproven counts.

Going deeper on one feature, with oracles and a mutation pass over the whole suite, is
`correctness-gate`. A feature whose checks pass but which nothing calls is `wire-check`. This skill
stands without either: without them, the loop above is the whole job.
