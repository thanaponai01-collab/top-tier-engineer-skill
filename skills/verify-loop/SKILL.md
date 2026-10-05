---
name: verify-loop
description: Build a check that can fail before the work, then loop until it passes, with retained proof. Use for "verify this change", "is it actually done?", work with no trustworthy check, reusable VERIFY.md recipes, testing whether a check would catch a wrong result, or fresh CI proof. Other skills hand it their claim and the wrong state it must reject.
---

# Verify Loop

Build the check before the work, make it hard to fool, and loop until it passes.

**Done** means: one mapped check was seen rejecting a controlled wrong result, the checks are
frozen with `baseline`, and `run --strict` then `status` print `VERIFY-STATE: green` on unchanged
inputs. Repairing a check that cannot fail and fixing the requested product defect are both part
of this task; finish both before reporting done.

## Pick the mode

| Situation | Read |
|---|---|
| Verify a task, diff, commit or branch | [verify this change](references/verify-change.md) |
| Ask whether an existing check would catch a wrong result | [challenge mode](references/challenge.md) |
| Set up CI or prove committed code fresh | [CI mode](references/ci.md) |
| The check has to launch and drive an app | [project recipe](references/project-recipe.md) |
| Schema, privacy, guardrail or repeatability checks | [compliance](references/compliance.md) |
| Another skill is handing you its claim | [handoff](references/handoff.md) |
| A reusable recipe, or none of the above | the loop below |

Verifying a change always means: fix the comparison point, trace the changed behavior into its
adjacent callers, reuse or extend the recipe, **run `verify.py challenge` on the highest-risk
check**, and finish with strict evidence and a coverage report.

Start from the task, not a full feature map. Read project instructions, manifests, tests and real
entry points, and reuse the project's harness. If VERIFY.md exists, check the affected sections
against the current app; if not, create only the sections the requested behavior and its adjacent
regressions need. A one-off request can end with direct checks and retained rejecting and passing
output. Strict green covers mapped claims only, never that every feature was found: report gaps.

## What makes a check good

1. **It can fail.** Observe rejection of a wrong result, restore, then observe a pass.
2. **It watches the real thing.** Run the program, hit the endpoint, or drive the UI.
3. **It does not come from the work.** Expectations come from the spec or claim, not the code.
4. **Its failure is specific.** It names expected versus actual.
5. **It is cheap to rerun.** One fast command.

## The loop

Resolve this skill's base directory from the loaded skill and run
`python <skill-base>/scripts/verify.py --help` before editing. The helper ships with the skill, not
the project; pass the project as its repo argument. With a VERIFY.md, direct tests supplement the
loop rather than replace it.

1. **Name the claim** in observable terms. "Refunds work" is a wish; "POST /refund on a paid order
   returns 200 and the balance drops by the amount" is a claim.
2. **Choose the strongest check you can afford.** Weakest to strongest: types and lint, unit,
   integration, a real run of the built thing, a run on real data. Take the top rung this
   environment can execute, plus one below it for a fast signal.
3. **Record it in VERIFY.md** ([format](VERIFY_FORMAT.md)): commands, `oracle:` files and a literal
   `fail-signal:`. `verify.py init` drafts a map from existing tests; finish it by regrouping by real
   feature, giving each in-scope feature a real-run check and listing what is left. An unfinished
   section stays unverified.
4. **Prove it can fail.** From a clean `git status` or a scratch worktree, put the code in the
   original bug or a deliberately wrong state and run `verify.py run`. The failure must be the
   declared `fail-signal:`, not a startup error or timeout. Restore, confirm `git diff` is empty, run
   again. The helper keeps the failing receipt; add a `fail-proof:` note describing the bad state.
   Strict needs one such receipt per mapped feature; prose alone does not count.
   A check that runs nothing (loads no cases, mocks what it tests, asserts nothing) is broken
   machinery: repair it here, keep what it *expects* as the spec says, prove it fails, and list the
   check files you changed for review.
5. **Freeze it.** `verify.py baseline`. From here the loop changes code, never the check.
6. **Work in slices, `verify.py run` after each.** Read the failure text and fix that.
   `NEWLY RED`: your last change broke a pass; undo or fix it first. `SAME FAILURE x2`: your picture
   is wrong; re-read code and output before a third try. `BUDGET` (five reds, `--budget` to tune):
   stop and report what passes, what fails and what you would try next.
7. **A check you believe expects the wrong thing is a finding, not an edit.** Say so and stop for a
   person, who reviews it and re-runs `baseline`. Editing it yourself gets `CHECK CHANGED` and a red
   run. (Repairing a check that never ran is step 4; changing what it expects is this step.)
8. **Finish:** `verify.py run --strict`, then `verify.py status` must print `VERIFY-STATE: green`,
   not `red`, `partial` (last run not strict), `stale` (inputs changed) or never-run. After adding or
   changing tests, `verify.py tests --strict` flags tests with no assertion, ones that pass either
   way, skipped ones and test files no feature names. Then look for what green cannot show: a
   feature with no section, a check never seen red (no rejection receipt or `fail-proof:` line, so
   unproven even when it passes), a deleted test, an output hardcoded to match.

## Fixing without disturbing

`verify.py scope <files>` names what the fix may touch, its test included. `OUT OF SCOPE` means
restore the stray edit or widen with `scope --add` and a reason; `KEEP-GREEN BROKEN` stays until the
earlier pass is back. `scope --clear` when done.

## Triage and evidence

- Before editing on a red, sort it: harness gap, spec drift or product gap ([triage](references/triage.md)).
- Keep redacted artifacts in `.verify-evidence/` or the project's own location; output tails
  survive teardown in `.verify-state.json`. Local state records runs; it does not stop a hostile
  writer. Independently owned CI does.
- Report the verdict first, then the `VERIFY:` line, the rejection you observed and the gaps.

```bash
python <skill-base>/scripts/verify.py init        # optional draft from existing tests
python <skill-base>/scripts/verify.py run         # run, retain failure evidence
python <skill-base>/scripts/verify.py run --affected  # run only features affected by git diff
python <skill-base>/scripts/verify.py run --stress 5  # detect flaky/non-deterministic checks
python <skill-base>/scripts/verify.py run --json  # machine-readable run report
python <skill-base>/scripts/verify.py baseline    # freeze checks and oracles
python <skill-base>/scripts/verify.py run --strict && python <skill-base>/scripts/verify.py status
python <skill-base>/scripts/verify.py status --json                       # same verdict, for callers
python <skill-base>/scripts/verify.py challenge . --feature F --auto app.py  # AST mutation score; never proof
```

Deeper oracles and mutation breadth: `correctness-gate`. Code nothing reaches: `wire-check`.

*Test:* the check was written before the change it judges, you can name the moment it was red, and
`status` reports green for unchanged final inputs.
