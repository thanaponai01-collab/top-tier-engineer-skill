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
   Then freeze the check: `verify.py baseline`. From here the loop fixes code and never the check.
5. **Do the work in slices, and run `verify.py run` after each.** Read the failure text and fix that.
   The run remembers the last one (`.verify-state.json`, gitignored) and says what one run cannot:
   `NEWLY RED` (your last change broke something that passed: undo or fix that first),
   `SAME FAILURE x2` (the same output twice: stop, your picture is wrong, re-read the code and the
   output before a third try), `BUDGET` (five red runs in a row, tune with `--budget`: stop and
   report what passes, what fails and what you would try next).
6. **A check you believe is wrong is a finding, not an edit.** If the code is right and the check is
   not, say so and stop for a person; they review it and run `verify.py baseline` again. Editing it
   yourself gets `CHECK CHANGED` and a failed run, even when everything else is green.
7. **Before you say done, run `verify.py status`.** It must print `VERIFY-STATE: green`: not `red`,
   not `stale` (files changed since the last run: run again) and not never-run. Then look for what a
   green cannot show: a test skipped or deleted, an output hardcoded to match. `--strict` for "done".

*Test:* the check was written before the change it judges, and you can name a moment it was red.

## Fixing one thing without disturbing the rest

An agent asked to fix X often re-edits Y, which already worked: it has no record of what worked and
nothing marks Y as off-limits. So before the first edit of a fix:

1. `verify.py run` for the state before. If nothing is green, or the thing you are about to touch has
   no check, write a check that pins its current behaviour first (it must pass now).
2. `verify.py scope <files or folders the fix may touch, its test included>`. This freezes what else
   is on disk and puts every passing check on watch.
3. Fix, and `verify.py run` after each slice. `OUT OF SCOPE  <file>` means you edited something you
   did not name: revert it. `KEEP-GREEN BROKEN` means something that worked when you began is red,
   and it repeats every run until it is green, so it cannot be waved off as already seen.
4. If the fix truly needs another file, `verify.py scope <file> --add` and say why in the report.
   `scope --clear` when the fix is done. `status` is not green while a file outside the scope differs.

*Test:* `verify.py scope --check` prints no OUT OF SCOPE line, and every check that was green at step 1 is green.

## Compliance checks

A check can also judge that the output is *allowed*, not only that it works. `scripts/compliance.py`
gives VERIFY.md four checks that exit 0 or 1, deterministic and stdlib-only:

| Kind | Command | Fails when |
|---|---|---|
| `schema:` | `compliance.py schema schema.json out.json --strict` | a field is missing, mistyped, out of range, or (with `--strict`) not in the schema; a schema keyword it cannot check is an error, never a pass |
| `privacy:` | `compliance.py privacy out/ logs/` | an email, card number, national ID, cloud key, token, private key or `password=` value is in the output (it prints where, never the value) |
| `guardrail:` | `compliance.py guardrail abuse.json -- <cmd>` | a case in `abuse.json` (`stdin`, `must_match`, `must_not_match`, `exit`) is not refused as written; an empty case list is an error |
| `repeat:` | `compliance.py repeat 3 -- <cmd>` | two runs of the same command print different output, so the suite is not deterministic |

Put the requirement in the schema or the case file *before* the code, from the requirement and not
from the output. A schema generated from the output only proves the code agrees with itself. Prove each
one can fail: feed it a bad file and watch it go red, then record that as the fail-proof.

## VERIFY.md

At the repo root. One `##` section per feature; each bullet is `kind: command`, and a check passes
when its command exits 0.

```
## Refunds
- test: `python -m pytest tests/test_refunds.py -q`
- run: `python scripts/smoke_refund.py`
- schema: `python scripts/compliance.py schema schemas/refund.json out/refund.json --strict`
- privacy: `python scripts/compliance.py privacy out/`
- fail-proof: changed the refund sign, test_refunds went red, reverted

## Journey: Buy something
- features: Login, Refunds
- test: `python -m pytest tests/test_buy_flow.py -q`
- fail-proof: broke the cart handoff, the flow test went red, reverted

## Run
- setup: `python scripts/seed.py`
- start: `python app.py`
- ready: `python scripts/wait_http.py http://localhost:8000/health`
- login: user demo@example.com, password in .env.test

## Blind spots
- the payment gateway is stubbed; real card declines are not exercised
```

**Journeys.** A feature can pass alone and fail with its neighbour, so the seams get their own
section: `## Journey: <name>`, `features:` naming two or more features that have their own sections,
and checks that run the whole flow (log in, then buy, then refund). A journey naming a feature with
no section, or fewer than two, is BROKEN and fails the run.

**Run.** A check that needs the app up needs a recipe for bringing it up, or the next session
guesses. `## Run` holds `setup` (seed data, run first), `start` (kept running in the background),
`ready` (exits 0 once the app is up), `stop` (optional; else the process tree is killed) and `login`
(free text). `verify.py run` does setup, start, waits for ready, runs the checks, and always stops
the app. If setup fails or the app never becomes ready, no check runs: a check against an app that
is not up proves nothing. Without a `## Run`, a `run:` check gets a note that it assumes the app is up.

`verify.py run` prints a result per feature (and per journey), then what a green run does **not** cover: features with
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
