---
name: verify-loop
description: Build a runnable check from the requested outcome, prove it rejects a wrong result, then loop until it passes. Use when a task has no trustworthy check, "done" was claimed without a run, a project needs a reusable VERIFY.md recipe, or the user asks to challenge existing verification with a controlled mutation. Discovers the recipe from the repo; no manual seed or complete feature map required.
---

# Verify Loop

Build the check before the work, make it hard to fool, and loop until it passes.

For a saved recipe, completion means a recorded expected rejection, a frozen baseline,
`run --strict` and current green `status`. Repairing an empty check and fixing the requested
product defect are authorized parts of this task; complete both before reporting done.

## Start with the task, grow the seed

Read existing project instructions, manifests, tests and real entry points. Reuse the project's
harness. If VERIFY.md exists, check the affected recipe against the current app; if absent,
create only the sections needed for the requested behavior and affected regressions. `init` is
an optional draft from tests, not discovery of every feature. FEATURES.md is an optional inventory.

The agent writes the seed; the user supplies the intended result. When VERIFY.md is absent,
one-off direct checks and retained rejection/passing outputs may suffice. Save the recipe for reuse
and grow it incrementally. A full map is useful for a requested audit or recurring verification.
Strict green proves mapped claims, never that every feature was discovered. Report remaining gaps.
For app driving, read [the project recipe](references/project-recipe.md): launch, doctor, drive,
evidence, cleanup. The file-backed loop below applies when saving a reusable recipe.

## What makes a check good

1. **It can fail.** Observe rejection of a wrong result, restore, then observe a pass.
2. **It watches the real thing.** Run the program, hit the endpoint, or drive the UI.
3. **It does not come from the work.** Write expectations from the spec/claim, not the implementation.
4. **Its failure is specific.** Pinpoint expected versus actual values.
5. **It is cheap to rerun.** One fast command.

## Challenge existing verification

When asked to challenge a check, read [challenge mode](references/challenge.md). Choose one
spec-backed product mutation and run `verify.py challenge` in scratch copies. Report caught,
survived or inconclusive with actual output. A diagnosis request ends with the finding; an
implementation request continues through check repair, the baseline and strict completion.

## The 7-step loop

Resolve this skill's base directory from the loaded skill, then run
`python <skill-base>/scripts/verify.py --help` before implementation edits. Use that helper with
the project as its repo argument; it is bundled with the skill, not necessarily in the project.
With an existing VERIFY.md, direct tests supplement the loop, rather than replace it.


1. **Name the claim.** What must be true when this is done, in terms you can observe. "Refunds work"
   is a wish; "POST /refund on a paid order returns 200 and the balance drops by the amount" is a claim.
2. **Choose the strongest check you can afford.** Weakest to strongest: types and lint, unit tests,
   integration tests, a real run of the built thing, a run on real data. Take the top rung this
   environment can execute, and add one below it for a fast signal.
3. **Record it in VERIFY.md** (see [VERIFY_FORMAT.md](VERIFY_FORMAT.md)). If tests already exist, `python <this skill's base
   directory>/scripts/verify.py init` drafts the feature map from them (it works in any folder, git or
   not). Then finish the draft: read
   the code behind relevant test files and regroup by real feature (one feature can span several
   test files, one file can cover several features); give each in-scope feature a real-run check,
   replace its TODOs and list the remaining gaps. An unfinished section stays unverified.
4. **Prove it can fail.** Run the finished feature check through `verify.py run` on the original bug
   or a deliberately wrong state. Read the failure: it must name the violated expectation, not a
   startup error or timeout. Restore the good state and run again. The helper retains the failing
   command, exit code, output and check hashes in .verify-state.json; strict verification requires
   this receipt plus a fail-proof note explaining the bad state. Prose alone cannot satisfy it.
   Prove at least one behavioral check per mapped feature; this does not certify every assertion.
   Declare `fail-signal:` as a literal expected-versus-actual rejection message before the negative
   run. Strict verification matches this against retained output and rejects common harness errors.
   Add the finished commands and `oracle:` files before the negative run so the receipt describes
   the same check that will judge the fix. Do this before the work, or on the working state,
   from a clean `git status` or a scratch worktree, and confirm the revert left an empty `git diff`.
   Then freeze the check: `verify.py baseline`. Include the spec, fixtures and smoke helpers under
   `oracle:`; tests, directly named script paths, check commands, failure signals and the Run recipe are frozen
   automatically. Imported helpers and expectation data must be listed explicitly; the runner cannot
   infer every dependency. Keep implementation
   files out of that list. From here the loop fixes code and never the check.
   A check that cannot fail because it runs nothing (it loads no cases, mocks the thing it tests,
   asserts nothing) is broken machinery, and repairing it before the freeze is part of this step, not
   an edit to make it pass. Leave what it *expects* as it was: an expected value comes from the claim
   or the spec, never from the code. Prove the repaired check can fail, freeze it, and list the check
   files you changed in the report so a person can review them.
5. **Do the work in slices, and run `verify.py run` after each.** Read the failure text and fix that.
   The run remembers the last one (`.verify-state.json`, gitignored) and says what one run cannot:
   `NEWLY RED` (your last change broke something that passed: undo or fix that first),
   `SAME FAILURE x2` (the same output twice: stop, your picture is wrong, re-read the code and the
   output before a third try), `BUDGET` (five red runs in a row, tune with `--budget`: stop and
   report what passes, what fails and what you would try next).
6. **A check you believe is wrong about what it expects is a finding, not an edit.** If the code is
   right and the check is not, say so and stop for a person; they review it and run `verify.py
   baseline` again. Editing it yourself gets `CHECK CHANGED` and a failed run, even when everything
   else is green. Repairing a check that never really ran is step 4; changing what a check expects so
   that it passes is this step.
7. **Before you say done, run `verify.py run --strict`, then `verify.py status`.** Status must print
   `VERIFY-STATE: green`: not `red`, `partial` (the last run was not strict),
   `stale` (file contents changed since the last run: run again) or never-run. Then look for what a
   green cannot show: a test skipped or deleted, an output hardcoded to match. `--strict` for "done".
   After adding or changing tests, run `verify.py tests --strict`: it lists every test function under the
   feature whose command names its file, and flags each with no assertion, each that catches its
   exception and passes either way, each skipped, and each in a file no feature names. A test with
   no row is one to give a row or to drop; a flagged one is a check that cannot go red (step 4).

*Test:* the check was written before the change it judges, and you can name a moment it was red.

## Fixing without disturbing (Scope Guard)

1. `verify.py run` to record the state before the fix.
2. `verify.py scope <files>` to name files the fix may touch, including its test.
3. Fix in slices. `OUT OF SCOPE` requires restoring the stray edit or explicitly widening scope
   with `scope --add` and a reason. `KEEP-GREEN BROKEN` remains until the previous pass is restored.
4. `verify.py scope --clear` when complete.

## Failure triage and evidence

- Categorize failures as harness gap, doc drift or product gap before editing; [TRIAGE.md](TRIAGE.md).
- Retain redacted runtime artifacts in `.verify-evidence/` or the project's existing location.
  Recorded output tails survive teardown in .verify-state.json. Local state is evidence of runs,
  not protection from a hostile writer; independently owned CI checks provide stronger separation.
- For schema, privacy, guardrail and repeat checks, read [COMPLIANCE.md](COMPLIANCE.md).
- Report verdict, the `VERIFY:` summary, meaningful rejection signals and coverage limits.

## Quick command reference

```bash
python scripts/verify.py init              # Optional draft from disk
python scripts/verify.py scaffold-driver   # Optional draft driver; not proof
python scripts/verify.py run               # Run checks and retain failure evidence
python scripts/verify.py baseline          # Freeze checks and declared oracles
python scripts/verify.py challenge . --feature Refunds --mutation mutation.json
python scripts/verify.py scope <files>     # Restrict allowed edit paths
python scripts/verify.py run --strict      # Require proof and complete mapped coverage
python scripts/verify.py status            # Require strict, green, current evidence
```

For deeper oracles and mutation checks, use `correctness-gate`; for unreachable code, `wire-check`.

*Test:* the same mapped check rejects a controlled wrong result, passes after restoration, and
`run --strict` followed by `status` reports green for unchanged final inputs.
