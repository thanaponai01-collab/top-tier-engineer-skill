# arch-design borrows from peer skills (4.53.0)

2026-10-08: SKILL.md gains: read recorded decisions first, ports only where earned, pin the deciding
numbers for a new design, tests move with the seam, ADR on a settled door, and the rejected second
store named with its cost. With-plugin arm only, semantic judge, claude-sonnet-5-5.

| case | result | before (2026-09-30) |
|---|---|---|
| arch-design-graph-shape | 1/1 pass | 2/2 |
| arch-design-verify-caller-count | 1/1 pass | 2/2 |
| arch-design-one-owner | 3/4 pass (one run proposed no merge, so no proof line) | 2/2 |
| arch-design-no-new-store | 1/4 pass (1/3 after the reworded reuse line) | 0/8 |

no-new-store still fails mostly on not naming what a second store would cost as the reason for
reusing the database; the runs that miss it do reuse `db.py`. Without-plugin arm not run. Also
fixed: `evals/agent.py` now resolves the Windows npm `claude.cmd` shim to `claude.exe`. Evidence:
`evals/results/arch-design-4.53/`.

# Callers on the verify-loop handoff (4.51.0)

2026-10-05: nine caller skills now point to `verify-loop/references/handoff.md` instead of each
restating it. With-plugin arm only, semantic judge, default model claude-sonnet-5-5.

| case | bare file pointer | final text (load verify-loop, record via its `verify.py`) |
|---|---|---|
| debug-protocol-regression-proof | fail: verify-loop never loaded, no `.verify-state.json` | 2/2 pass |
| build-discipline-verified-slice | fail: verify-loop never loaded, no `.verify-state.json` | 2/2 pass (one more try lost to a runner file-lock error, not graded) |
| correctness-gate-green-but-wrong | pass | 1/1 pass |
| wire-check-orphan-and-decoy | pass | 1/1 pass |
| perf-optimize-n-plus-one-and-decoy | pass | 1/1 pass |
| threat-model-client-role-and-decoy | pass | 1/1 pass |
| safe-release-migration-loses-data | pass | 1/1 pass |
| safe-release-combined-migration-and-decoy | pass | 1/1 pass |
| debug-protocol-distant-cause | pass | 1/1 pass |

evolve-maintain and agent-release still have no behavioral case. Evidence:
`evals/results/verify-handoff-callers*/`.

# verify-loop rewrite (4.50.0)

2026-10-05: SKILL.md restructured (148 -> 108 lines) and `references/handoff.md` added. All eight
verify-loop cases ran once with the plugin (semantic judge, default model claude-sonnet-5-5).

| case | first pass | after restoring two cut lines |
|---|---|---|
| verify-loop-check-is-wrong | pass | not rerun |
| verify-loop-check-cannot-fail | pass | not rerun |
| verify-loop-make-it-verified | pass | not rerun |
| verify-loop-fake-check-and-decoy | pass | not rerun |
| verify-loop-challenge-survivor | pass | not rerun |
| verify-loop-ci-fresh-proof | pass | not rerun |
| verify-loop-green-with-unverified | fail: missed "existing checks never shown red" | 2/2 pass |
| verify-loop-change-shared-caller | fail: no `challenge` verdict recorded | 2/2 pass |

The fixes added text only (an inline challenge step for change verification; unproven checks
listed under what green cannot show), so the six first-pass results stand for the final text but
were not re-sampled. Without-plugin arm not run. Evidence: `evals/results/verify-loop-rewrite/`,
`evals/results/verify-loop-rewrite-2/`.

# Verification handoffs across seven specialist skills

Follow-up on 2026-10-05: added conditional verify-loop handoffs to correctness-gate,
wire-check, perf-optimize, threat-model, safe-release, evolve-maintain and agent-release.
Each preserves specialist ownership and a direct-check fallback. Two existing description
values (evolve-maintain and agent-release) were quoted to make their YAML valid.

Six existing with-skill smoke cases ran once each, with phrase/action grading and no semantic
judge: four passed; correctness-gate-green-but-wrong and
safe-release-combined-migration-and-decoy failed phrase grading. The retained reports identify
the primary defects and give fail/hold verdicts, but omit exact filenames or phrases expected
by the grader. Those failures remain recorded rather than being reclassified as passes.

Evidence: `evals/results/2026-10-05-2159/`. The runner staged the skills before final paragraph
placement and frontmatter repairs. These samples check existing specialist workflows, not
end-to-end completion of the new handoffs. Evolve-maintain and agent-release have no existing
behavioral cases; their new handoffs remain behaviorally unverified. All seven final skills
pass quick validation. All 350 repository unit tests pass, including eight standalone checks.

## Generated smoke scorecard

# Scorecard — do the skills make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. This batch ran each task once **with**
the plugin; the without-plugin arm was not run.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

This batch used phrase and action grading (`--no-judge`). No separate semantic judge ran.

- **When:** 2026-10-05-2159
- **Model:** claude-sonnet-5-5
- **Tries per case, per side:** 1
- **Plugin version:** 4.49.0
- **Cost of this run:** $1.04
- **Raw evidence:** `evals/results/2026-10-05-2159/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `correctness-gate-green-but-wrong` | `correctness-gate` | the tests pass — is the code correct? | — | 0 of 1 | only one side was run |
| `perf-optimize-n-plus-one-and-decoy` | `perf-optimize` | what happens to this dashboard as the customer count grows? | — | 1 of 1 | only one side was run |
| `safe-release-combined-migration-and-decoy` | `safe-release` | go / no-go on this release plan? | — | 0 of 1 | only one side was run |
| `safe-release-migration-loses-data` | `safe-release` | green tests and a written migration — is it safe to ship, and does it leave production alone while deciding? | — | 1 of 1 | only one side was run |
| `threat-model-client-role-and-decoy` | `threat-model` | what can a signed-up customer account be made to do here? | — | 1 of 1 | only one side was run |
| `wire-check-orphan-and-decoy` | `wire-check` | what does this system serve, and what reaches nothing? | — | 1 of 1 | only one side was run |

**Did the agent open the skill it was asked to use?** 6 of 6 tries.
A try that never opened the skill measured the model, not the skill.

## Why tries failed

- `correctness-gate-green-but-wrong` **with**: missed: test_hundred asserts fee(100) == 5, which is what the code does rather than what the spec says; missed: correctness is judged against SPEC.md, not against the existing suite
- `safe-release-combined-migration-and-decoy` **with**: missed: 002_migrate_total_to_cents.sql adds total_cents, backfills it, and drops total all in one script/deploy, with app.py switching reads in the same release — no separate expand/backfill/contract deploys; fell for the trap: 001_add_notes_column.sql is purely additive (nullable column, no backfill) and is safe/reversible on its own; it is not part of the risk in 002

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever a skill or the model changes.


## Previous evaluation record

# Build and debug verification integration

Follow-up on 2026-10-05: build-discipline now keeps slice progress in BUILD.md while reusable
VERIFY.md recipes finish through verify-loop. Debug-protocol separates diagnosis-only completion
from authorized fixes, carrying the proven cause into retained regression rejection and strict proof.
The verifier itself is unchanged; native-check fallbacks and independent skill use remain available.

| Case | Without skill | Final with-skill |
|---|---|---|
| build-discipline-verified-slice | product checks passed; retained strict proof absent | passed strict proof, BUILD.md and independent wrong/original replays |
| debug-protocol-regression-proof | not run | passed retained rejection, strict proof and independent wrong/original replays |
| debug-protocol-distant-cause | not rerun | proved cause and left diagnosis-only source unchanged |

Baseline: `evals/results/2026-10-05-2130/`. Pilot: `evals/results/2026-10-05-2131/`.
The build pilot omitted BUILD.md; the instruction and artifact gate were tightened. Its initial
pass predates that gate and is not the final acceptance result. The debug pilot did not load its
skill because the existing description contained invalid YAML. That frontmatter was repaired.
Final build: `evals/results/2026-10-05-2132/`; final debug cases:
`evals/results/2026-10-05-2133/`. Diagnosis-only preservation was also checked against the retained
workspace; final-workdir-grade.txt records that result. Existing gateway limits remain intact.

These are workflow-completion smoke samples, not diagnostic superiority or a reliability estimate.
The plain build agent also implemented working behavior. Phrase/artifact grading was used, without
semantic judging. The new fixtures exercise a CLI entry point and native Python checks; service,
security and performance integrations remain future work. All 350 unit tests, 37 focused eval-grader tests and skill frontmatter validation pass.

## Earlier project setup evaluation

Follow-up on 2026-10-05: project-setup now refreshes an existing partial recipe, discovers native
commands, preserves manual notes and validates selected behavior through the unchanged verify-loop.

| Case | Without skill | With skill |
|---|---|---|
| Python existing partial setup | preserved notes and ran native checks; no retained strict proof | passed strict/rejection/preservation gates |
| Node CommonJS partial setup | not run | passed strict/rejection/preservation gates |

The Python baseline is `evals/results/2026-10-05-2031/`; with-skill evidence is
`evals/results/2026-10-05-2033/`. Node pilot evidence is `evals/results/2026-10-05-2035/`.
The pilot repeated validation but did not fully repeat discovery; the instruction was clarified.
The final Node run (`evals/results/2026-10-05-2037/`) re-read project inputs and confirmed unchanged
setup hashes and a single instruction pointer. Both native checks independently rejected supplied
wrong implementations and passed originals; final-workdir-grade.txt retains those replay results.
Product files, original tests and manual notes were preserved in both successful runs.

This shows completion of a reusable proof workflow, not superior diagnosis. The plain Python agent
also preserved notes and made useful setup files. Samples are one run each, use phrase/artifact
grading without a semantic judge, and do not establish reliability across arbitrary stacks.
Go, Rust, dependency-bearing monorepos, missing prerequisites, services and CI provisioning were
not live-tested in this setup evaluation; the skill reports such gaps explicitly. CI runner evidence
below remains separate. All 350 repository tests, 37 focused eval-grader tests and skill validation pass.

## Earlier verification workflow evaluation

Fresh-CI follow-up on 2026-10-05. Both the plain agent and the with-skill agent rejected
a weak check despite a copied local green state. The with-skill run invoked the new CI
helper on locally committed inputs and produced a red report with the candidate commit,
surviving mutation, stage results and output. No product, check or spec was edited.

This is evidence that the mode is usable, not a diagnostic advantage over the baseline.
The CI CLI regressions separately require correct committed inputs to pass and reject
surviving mutations, bad products, dirty checkouts and empty plans. They also require
local state to remain unchanged and never appear in the generated proof.

- Plain evidence: `evals/results/2026-10-05-2007/`.
- With-skill evidence: `evals/results/2026-10-05-2009/`.
- Both runs passed the final case grading after removing a phrase that echoed the prompt.
- No semantic judge was used. One run per arm is not a reliability estimate.
- All 349 unit tests pass; the skill validator also passes.
- The real nested example exposed a Git archive working-directory prefix bug; a failing
  subdirectory regression was added and the export now runs at the Git root. The example
  passes from a clean clone. All 350 unit tests and 7 focused CI checks pass.
- [Hosted workflow run](https://github.com/thanaponai01-collab/top-tier-engineer-skill/actions/runs/37315843975)
  passed both jobs, including all 350 tests on Ubuntu with Python 3.12.
  Downloaded report, state and log identify candidate commit
  `7011929684442d638a4996835e6244f343471dde` and project `examples/verify-ci`.
  Baseline, challenge, strict run and status all exited zero; the mutation was caught
  and the final state was strict green.
- The workflow pins verifier commit `06f0e7a6b68a5a68b9c35835938bd93300425924`.
  Its recorded verifier SHA256 matched the three scripts at that commit:
  `8771d5a51b076ed4a613ce0c623b1776b6276ccddd9c9fd411adcb62840761e9`.
  This proves the example's selected claim and mutation. Candidate-owned expectations
  still require review; fresh execution does not establish independent oracle ownership.

## Earlier change verification evaluation

Verify-this-change follow-up on 2026-10-05. The new case supplies a diff changing a
shared threshold. The with-skill agent traced both callers, repaired the adjacent
discount regression, added meaningful boundary checks, caught shipping and discount
mutations, and completed current strict verification. It retained the intended
shipping behavior and reported the supplied comparison point and coverage limits.

| Case | Without skill | With skill |
|---|---|---|
| verify-loop-change-shared-caller | product and regression checks passed; no reusable strict/challenge evidence | 1/1 passed all artifact and independent outcome gates |
| verify-loop-make-it-verified | not rerun in this pass | 1/1 completed strict verification |

The plain agent also found and fixed the adjacent regression. The measured difference
is completion of the reusable verification workflow, not superior diagnosis.
The final baseline allows its related runner script; it still fails the evidence gates.
These are smoke samples, not a reliability estimate. No semantic judge was used.

- With-skill evidence: `evals/results/2026-10-05-1921/` (rescored against final case wording).
- Final baseline: `evals/results/2026-10-05-1924/`.
- Initial baseline pilot: `evals/results/2026-10-05-1919/`.
- All 343 unit tests and the skill frontmatter validator pass.
- Five grader regressions reject weak adjacent checks, missing evidence, incorrect product
  behavior and removal of the adjacent feature; the executed reference solution passes.
- Sequential challenge receipts now survive later feature challenges without crediting
  unselected features. Changed check signatures still invalidate old proof.
- The live case exercises a supplied diff in a non-Git folder. Git commit/range discovery
  remains agent-guided; it was not separately measured in this smoke evaluation.

## Earlier challenge evaluation

Challenge mode follow-up on 2026-10-05. The final challenge smoke test loaded the
skill, invoked the bundled helper and retained a surviving verdict with both
trial results. Source files stayed unchanged. The grader independently replayed
the unchanged check against the wrong implementation.

| Case | Without skill | With skill |
|---|---|---|
| verify-loop-challenge-survivor | diagnosed correctly; required evidence was written outside fixture/ | 1/1 passed all artifact and outcome gates |
| verify-loop-make-it-verified | 0/1 completed the workflow | 1/1 completed strict verification |

The plain agent also detected the vacuous check. Its artifact failure is a workflow
compliance difference, not evidence that the skill improves diagnosis. Earlier
challenge pilots had a less explicit evidence schema; their failures likewise
must not be presented as diagnostic wins. These are tiny smoke samples, not a
reliability estimate. Phrase grading and artifact checks were used; no semantic judge.

- Final challenge evidence: `evals/results/2026-10-05-1906/`.
- Existing-loop regression and challenge pilot: `evals/results/2026-10-05-1903/`.
- Initial baseline pilot: `evals/results/2026-10-05-1901/`.
- All 337 unit tests pass, including 11 challenge CLI regressions.
- CLI regressions cover caught, survived, inconclusive, frozen targets, invalid mutations,
  overwritten mutations, unchanged source/state, strict receipt reuse and feature isolation.
- One caught mutation proves detection of that mistake; external service isolation remains
  the project's responsibility. Scratch copies are not an OS sandbox.

## Earlier verification hardening evaluation

Follow-up on 2026-10-05: the stricter case requires a frozen baseline and a current,
strict green helper status, alongside broken/correct implementation replays.
One with-skill run passed all gates; one without-skill run failed. The successful
agent repaired the empty check, recorded a behavioral rejection, froze its checks,
fixed refunds and completed strict verification. This is a smoke test, not a
reliability estimate. Phrase grading and artifact checks were used; no semantic judge.

Evidence: `evals/results/2026-10-05-1839/`. Approximate cost: $0.37.
All 326 unit tests pass, including the two reproduced false-green regressions.
The runner now freezes directly named helpers and requires a declared failure signal.
Imported helpers and expectation files still need explicit oracle declarations.

## Earlier evaluation (weaker completion gates)

Targeted evaluation on 2026-10-05 (Asia/Bangkok), using Claude Code's default model
(`claude-sonnet-5-5`). This run used phrase grading (`--no-judge`), action/artifact checks,
and replay of the agent's check against broken and correct implementations. No semantic judge
was run. These are small-sample smoke evaluations, not a reliability estimate.

| Case | Without skill | With skill, grader verdict | Full helper workflow observed |
|---|---|---|---|
| verify-loop-make-it-verified | 0 of 1 | 3 of 5 | 2 of 5 |

The first two skill runs repaired the vacuous check, recorded an actual failure, froze the
checks, fixed the product and ran strict verification/status successfully. The plain run only
diagnosed the problem and asked whether to fix it.

After integrating the upstream document split, run 3 repaired the check and product but skipped
the helper; the case grader passed its outcome because freezing is advisory in that case.
Treat its workflow as incomplete. Run 4 also skipped the helper and omitted the proof note.
The final run (5), with the original detailed steps restored and helper location explicit,
ran helper help and exposed the faulty check, but stopped before the product fix and final loop.
It asked for permission despite the task requesting verified refunds.

**Final limitation:** the verifier's executable checks pass, but the final live skill evaluation
does not establish reliable autonomous completion. Preserve this limitation rather than infer
reliability from the earlier successful runs. The final merged code passed all 323 unit tests.

- Raw evidence: `evals/results/2026-10-05-1741/` (reports, action logs, grades and results).
- Total evaluation cost: approximately $1.22.
- Plugin version evaluated: 4.49.0.
- Every with-skill run loaded the skill; transcripts stay local per .gitignore.

Reproduce with `python evals/run.py --cases verify-loop-make-it-verified --repeats 1`.
