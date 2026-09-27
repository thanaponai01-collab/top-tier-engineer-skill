# Scorecard — do the skills make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-09-27-0710
- **Model:** claude-haiku-4-5-20251001, claude-opus-5-5
- **Tries per case, per side:** 6
- **Plugin version:** 4.39.0
- **Cost of this run:** $24.17
- **Raw evidence:** `evals/results/2026-09-27-0657/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `arch-design-no-new-store` | `arch-design` | how should CSV export and its history be structured, and which decision here is expensive to get wrong? | 0 of 6 | 3 of 6 | **skill helps** |
| `arch-design-one-owner` | `arch-design` | where did the structure go wrong, and what is the top move? | 0 of 6 | 4 of 6 | **skill helps** |
| `arch-design-verify-caller-count` | `arch-design` | is the shipping seam safe to inline, and what changes if so? | 6 of 6 | 6 of 6 | no difference — the agent already does this |
| `correctness-gate-green-but-wrong` | `correctness-gate` | the tests pass — is the code correct? | 5 of 6 | 5 of 6 | no clear difference |
| `debug-protocol-distant-cause` | `debug-protocol` | the total is wrong where it is printed — where does it actually go wrong? | 2 of 6 | 6 of 6 | **skill helps** |
| `drive-bug-through-skills` | `drive` | a bug goal with no known cause: is the run diagnosis first, then a fix, then proof, each through the skill that owns it? | 3 of 6 | 6 of 6 | **skill helps** |
| `drive-overnight-parks-the-deploy` | `drive-overnight` | working alone, does it fix the bug but leave the one-way step the repo tells it to take for a person? | 6 of 6 | 6 of 6 | no difference — the agent already does this |
| `latent-audit-layers-and-decoy` | `latent-audit` | what is dead, and are the layers respected? | 6 of 6 | 2 of 6 | **skill hurts** |
| `safe-release-migration-loses-data` | `safe-release` | green tests and a written migration — is it safe to ship, and does it leave production alone while deciding? | 2 of 6 | 5 of 6 | **skill helps** |
| `structure-gate-opaque-not-clean` | `structure-gate` | three tiny functions — is it clean? | 0 of 6 | 6 of 6 | **skill helps** |
| `wire-check-orphan-and-decoy` | `wire-check` | what does this system serve, and what reaches nothing? | 4 of 6 | 4 of 6 | no clear difference |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
87 of 132 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 66 of 66 tries.
A try that never opened the skill measured the model, not the skill.

**Did the agent follow the skill's own steps?** Scored apart from the table above, because
only the side with skills can be asked it:
- `drive-bug-through-skills`: 1 of 6 tries — went through the playbook: opened drive → debug-protocol → evolve-maintain → correctness-gate, in order, rather than doing the steps from memory.
  - one try opened: drive
  - one try opened: drive → debug-protocol → evolve-maintain
  - one try opened: drive
  - one try opened: drive → evolve-maintain → correctness-gate
  - one try opened: drive

## Why tries failed

- `arch-design-no-new-store` **with**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **with**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **with**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **without**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **without**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **without**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **without**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **without**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-no-new-store` **without**: missed: the report names what a separate new datastore would cost if it turned out wrong — a migration, a second thing to secure and back up — as the reason for reusing the existing database
- `arch-design-one-owner` **with**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **with**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `arch-design-one-owner` **without**: missed: the top move is written out with the callers it changes and the check that behaviour did not
- `correctness-gate-green-but-wrong` **with**: missed: correctness is judged against SPEC.md, not against the existing suite
- `correctness-gate-green-but-wrong` **without**: missed: correctness is judged against SPEC.md, not against the existing suite; fell for the trap: the gate must fail; a green suite is not evidence of correctness here
- `debug-protocol-distant-cause` **without**: missed: the cause was proven in both directions, not just observed once; did not do it: reproduced the failure before changing any code (changed the code first; ran it only afterwards)
- `debug-protocol-distant-cause` **without**: missed: the cause was proven in both directions, not just observed once
- `debug-protocol-distant-cause` **without**: did not do it: reproduced the failure before changing any code (changed the code first; ran it only afterwards)
- `debug-protocol-distant-cause` **without**: missed: the cause was proven in both directions, not just observed once
- `drive-bug-through-skills` **without**: did not do it: reproduced the failure before fixing it (changed the code first; ran it only afterwards)
- `drive-bug-through-skills` **without**: did not do it: reproduced the failure before fixing it (changed the code first; ran it only afterwards)
- `drive-bug-through-skills` **without**: did not do it: reproduced the failure before fixing it (changed the code first; ran it only afterwards)
- `latent-audit-layers-and-decoy` **with**: missed: app/services/legacy_export.py is referenced nowhere, by import or by string — the one real deletion candidate
- `latent-audit-layers-and-decoy` **with**: missed: app/services/legacy_export.py is referenced nowhere, by import or by string — the one real deletion candidate
- `latent-audit-layers-and-decoy` **with**: missed: app/services/legacy_export.py is referenced nowhere, by import or by string — the one real deletion candidate
- `latent-audit-layers-and-decoy` **with**: missed: app/services/legacy_export.py is referenced nowhere, by import or by string — the one real deletion candidate
- `safe-release-migration-loses-data` **with**: missed: the safe shape: add and copy first, switch reads, drop the old column in a later, separate release
- `safe-release-migration-loses-data` **without**: missed: the safe shape: add and copy first, switch reads, drop the old column in a later, separate release
- `safe-release-migration-loses-data` **without**: missed: the safe shape: add and copy first, switch reads, drop the old column in a later, separate release
- `safe-release-migration-loses-data` **without**: missed: the safe shape: add and copy first, switch reads, drop the old column in a later, separate release
- `safe-release-migration-loses-data` **without**: missed: the safe shape: add and copy first, switch reads, drop the old column in a later, separate release
- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict; fell for the trap: the entered 5% is genuinely simple; calling the codebase clean on that basis is the wrong answer
- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict; fell for the trap: the entered 5% is genuinely simple; calling the codebase clean on that basis is the wrong answer
- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines
- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict
- `structure-gate-opaque-not-clean` **without**: missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict
- `structure-gate-opaque-not-clean` **without**: missed: dashboard.py holds 230 lines of JavaScript inside a string literal that no parser, linter or test can enter; missed: the fraction actually measured is reported before any finding — about 5% of the code lines; missed: the unmeasured part is reported as unknown, not folded into a clean verdict
- `wire-check-orphan-and-decoy` **with**: missed: two ways in exist: app.py dispatch and scheduler.py cron. Missing the scheduler turns digest into a false orphan
- `wire-check-orphan-and-decoy` **with**: missed: two ways in exist: app.py dispatch and scheduler.py cron. Missing the scheduler turns digest into a false orphan
- `wire-check-orphan-and-decoy` **without**: missed: two ways in exist: app.py dispatch and scheduler.py cron. Missing the scheduler turns digest into a false orphan
- `wire-check-orphan-and-decoy` **without**: missed: two ways in exist: app.py dispatch and scheduler.py cron. Missing the scheduler turns digest into a false orphan

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever a skill or the model changes.
