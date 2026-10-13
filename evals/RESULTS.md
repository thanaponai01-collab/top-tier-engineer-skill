# Task-context retrieval revision — 2026-10-13

These local, uncommitted instruction changes were checked with real agents. This is one trial
per case/arm, not a reliability estimate or proof of improvement over the baseline.

| Case | Without plugin | With revised plugin | Evidence |
|---|---|---|---|
| project-context-task-trail | 1/1 pass | 1/1 pass on final instructions | results/context-task-trail-baseline/; results/context-task-retrieval-final/ |
| project-context-stale-evidence | not rerun | 1/1 pass on final instructions | results/context-task-retrieval-final/ |
| project-foundation-after-setup | not rerun | 1/1 pass | results/context-task-retrieval-with/ |
| build-discipline-keeps-decisions | not rerun | 1/1 pass | results/context-task-retrieval-with/ |
| pick-skill-slow-is-a-bug | not rerun | 1/1 pass | results/context-task-retrieval-with/ |

The initial with-plugin batch also passed both context cases, before the task procedure was split
into references/task-context.md to meet the context budget. Its retained evidence is in
results/context-task-retrieval-with/. The final context replay loaded project-context via the
Skill tool and read task-context.md, then inspected relevant Git history and reran the safe check.
The foundation transcript records an actual startup-pointer write to the installed Task context
reference. The building regression passed, but does not prove every working skill follows the
shared context procedure or that larger projects load only relevant areas.

Repository checks: all 484 tests passed in 95.661 seconds; catalog listing 4993/5000 characters;
handoff check: no budget overruns or structural gaps. A first full run caught a missing frontmatter
trigger phrase; corrected and rerun. Structural/cache checks are not product or behavior proof.

Record-format/indexing detail was subsequently moved unchanged into references/storage.md so
memory.md also fits the context helper's stricter 80-line detail budget. Scoped structural checks
pass and the 20 context-instruction tests pass. Replay evidence: results/context-task-storage-split/.
The latest broad handoff check observes concurrently added work/pstack-handoff.md and reports
an unrelated missing packages/auth/VERIFY.md link from skills/verify-loop/VERIFY_FORMAT.md;
that work was not changed here. The earlier clean handoff result predates those workspace changes.

Historical scorecards below retain their original claims and limitations.

# Scorecard - do the skills make an agent better?

Each row is one rigged codebase from `evals/cases/`: a real defect planted in it, and a
trap beside it that a careless agent falls for. A real agent was given the task several
times **without** this plugin (plain Claude Code, the task in plain words) and **with** it.
A try counts as passed only if the agent found everything planted, fell for no trap,
and actually did the work its report claims (checked from its own transcript).

Reports are graded on **meaning** by a separate model that is never told which side wrote
them, and must quote the report for every finding it credits; a quote that is not really in
the report does not count. That judge grades every reference report correctly
(`python evals/judge.py --calibrate`).

- **When:** 2026-10-13-1147
- **Model:** claude-opus-5-5
- **Tries per case, per side:** 1
- **Plugin version:** 4.61.1
- **Cost of this run:** $0.20
- **Raw evidence:** `evals/results/2026-10-13-1147/` — every report, action log and grade

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `recall-stale-proof` | `recall` | what is the true state of the work: what the notes claim, checked against what can be rerun now? | — | 1 of 1 | only one side was run |

**Meaning vs phrase grading:** the older phrase grader (`grade.py`) agreed with the judge on
1 of 1 reports. Where they differ, open the run's `grade.txt`: both verdicts are there.

**Did the agent open the skill it was asked to use?** 0 of 1 tries.
A try that never opened the skill measured the model, not the skill.

## Why tries failed

None failed.

## How to read this

- **Skill helps**: with the skill the agent passes clearly more often. The skill earns its place.
- **No difference — the agent already does this**: the model gets it right on its own. The
  skill costs attention and adds nothing on this task; make the case harder or cut the skill.
- **Skill hurts**: the agent does worse with the skill. Fix it before anything else.
- A few tries is a small sample. One try either way is noise; a gap of two or more in three is a signal.

Re-run with `python evals/run.py` whenever a skill or the model changes.

## Previous scorecard (historical evidence)

# arch-design for an owner who can't read code (4.61.0)

2026-10-11: SKILL.md becomes map, scope, candidates, deep dive, record, with before/after pictures
and a stop to ask. New case `arch-design-stale-map-owner-view`. Isolated, semantic judge.

| case | before | after (final SKILL.md) |
|---|---|---|
| arch-design-stale-map-owner-view | old skill 0/2, no skill 0/2 | 7/7 after the opener fix (one earlier run left Windows cache files in the repo; judge 5/5 on its report) |
| arch-design-graph-shape | 1/1 (4.53) | 2/2 |
| arch-design-one-owner | 3/4 (4.53) | 2/2 |
| arch-design-verify-caller-count | 1/1 (4.53) | 2/2 |
| arch-design-no-new-store | 1/4 (4.53) | 1/2, still misses naming the cost of a second store |

Baseline misses: no before/after picture (3 of 4) and no question back to the owner (3 of 4); all
four found the email chain. Plain-arm transcripts checked: neither read the plugin. Evidence:
`evals/results/2026-10-11-arch-owner-{baseline,new,final}/`.

# Every skill has a case; evals isolated from the person's install (unreleased)

2026-10-11: 17 new cases cover the last uncovered skills (`uncovered.txt` is empty). Every reference
set discriminates on the phrase grader, and the semantic judge read 51/51 new references correctly.

**The harness was measuring the installed plugin.** Each eval agent inherited user settings:
the person's enabled top-tier-engineer (marketplace 4.58.1) and `~/.claude/CLAUDE.md`. The
"without" arm opened skills on its own, and both arms got PHILOSOPHY.md's "work directly" nudge.
Isolated, live routing rose from 11/34 to 21/34 (ROUTING.md).
`agent.build_command` now passes `--setting-sources project,local` (regression-tested). The first
batch is kept as `results/coverage-2026-10-11-contaminated/`. Earlier rows in this file ran under
the same leak and should be read with that in mind.

Isolated, claude-sonnet-5-5, semantic judge, 1–2 tries per arm ($3.42):

| result | cases |
|---|---|
| skill helps (plain arm failed both tries) | agent-release, arch-map, issue-handoff, pick-skill, problem-framing |
| no difference (both pass) | agent-design, agent-drift, agent-evals, agent-prove, agent-trace, code-history, evolve-maintain, explain, feature-map, recall |
| skill hurt once | scrutinize: 1 of 2 runs switched the person's checkout between branches |
| unmeasured | onboard-system: the judge flips on identical text for the invariant item |

Per-case table and reading: `docs/context-gaps.md`. Evidence: `evals/results/coverage-2026-10-11/`.

# Setup and update context upkeep (4.56.0)

2026-10-09: project-setup now saves missing intent/work context, preserves equivalent documents,
and checks structural completeness; maintenance/build workflows link one shared upkeep reference.
The context checker keeps legacy budget mode and adds --check-handoff for startup markers,
nonempty intent/work, Next and local document/include links. Unfinished areas remain current
through work/ includes rather than being archived as completed proof.

Live setup runs initially failed because project-setup is manual-only and the agents reported
the skill unavailable. The evaluation harness now supplies the staged SKILL.md path for explicitly
requested manual-only skills, without exposing answer keys or findings. This preserves the skill's
invocation policy. The initial failures are retained in evals/results/context-setup-upkeep/.
Its model-invoked build-discipline-keeps-decisions run passed 1/1 ($0.19).

With explicit invocation, project-setup-existing-project and project-setup-node-project passed
1/1 each ($0.26 and $0.22). Their strengthened finished-workspace checks require saved intent,
an actionable Next section and startup pointers, in addition to existing product-preservation,
strict verification and independently replayed wrong/original checks. Both agents retained manual
coverage limits. Evidence: evals/results/context-setup-explicit/. Phrase grading was used with
finished-workspace checks, without a semantic judge. These single runs are not a reliability estimate.
Final full suite: 411 tests passed. Seven related installed Codex skills were backed up and synced;
the installed shared reference and context checker match the repository hashes.

# Decisions outlive the session (4.55.0)

2026-10-09 follow-up (unreleased): `build-discipline-keeps-decisions` passed 1/1 with the updated
skills, using phrase grading and finished-workspace checks; $0.20, 40 seconds. Evidence:
`evals/results/context-handoff-regression/`. No semantic judge was used. A separate two-session
volume/intent handoff is documented in `evals/context-handoff/README.md`; the artifact checker
retains 35 active decisions and 200 controlled replay receipts, and rejects a missing active
decision. All 401 repository tests passed. This small sample is not a reliability estimate.
The independent fresh reader recovered the intended JSON behavior and identified that the green
CSV baseline did not establish JSON acceptance; its sourced capsule is retained in
`evals/context-handoff/reader-report.md`. Startup notes were 26/120 and 19/80 lines after compaction.

2026-10-09: new case `build-discipline-keeps-decisions`. Mid-build, the user mentions in passing
that the export format changed (CSV → JSON). The case is graded on the brief left behind: it states
JSON, no line still presents CSV as current, and `CLAUDE.md` sends a fresh session to it. Building
the JSON export is advisory. Both arms, semantic judge, claude-sonnet-5-5, 3 tries each.

| run | without skills | with skills |
|---|---|---|
| skills before this release | 0/3 | 0/3 (1 of 3 recorded the decision; none linked the brief) |
| first draft of the new text | not rerun | 0/3 on the old grader; under the corrected one, 2/3 (the third added no `CLAUDE.md` link) |
| final text | **0/3**: brief left saying CSV, nothing links it | **3/3** |

Plain agents built the month slice, said in the report that JSON was pending, and left `BRIEF.md`
still preferring CSV. That is the forgetting this release targets. Two grader fixes came from real
reports, not from wanting a pass: the "no line still says CSV" check had rejected "(changed …; was
CSV)" and an assumptions row about "the same fields as the CSV columns". Both sentences are now unit
tests. Neither fix changes a plain-arm result, since those failed the "brief names JSON" check
anyway. A first draft of the prompt ("I don't want the next session drifting back to CSV") gave the
answer away: plain agents passed it 2/2, so it was rewritten. Evidence:
`evals/results/keeps-decisions-{v1-leaky-prompt,before,after,final}/`.

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

## Project memory evaluation attempts

Baseline and with-skill runs could not execute: Claude session usage limit.
See results/project-memory-baseline and results/project-memory-with. These runner failures
provide no behavioral validation. Updated cases require a fresh baseline and with-skill run.

## Complete foundation refresh attempt

Six Haiku runs (without/with for full-foundation, existing-project setup and project-update) all
returned Claude's session usage limit before performing work. See results/full-foundation-refresh.
No behavioral baseline failure or skill improvement is established. Native plugin validation and
helper/unit tests are separate evidence; rerun the final cases after account usage is available.

## Scaling trials (2026-10-11)

Single trials with Claude Code default model; raw evidence: `evals/results/2026-10-11-0008/`.

| Case | Skill | What it tests | Without skills | With skills | Verdict |
|---|---|---|---|---|---|
| `project-context-stale-evidence` | `project-context` | Can bounded retrieval distinguish historical login evidence from current verification? | 1 of 1 | 1 of 1 | no difference â€” the agent already does this |
| `project-setup-full-foundation` | `drive` | Does one setup prepare linked sourced architecture, commands and bounded memory alongside existing verification without changing the product? | 0 of 1 | 1 of 1 | **skill helps** |


## Context scaling follow-up

The corrected expanded project-update-preserves-intent trial ran separately in
`evals/results/2026-10-11-0009/`: both arms passed 1/1, with allowed-file and area-content checks.
The skill-loaded arm updated auth/shared records, preserved the unrelated invoice backlog and
kept verification unproven. No improvement over the baseline is established by this one trial.
Its report states repeat upkeep required no edits; a distinct post-edit re-read is not visible in
the action log, so independent idempotence proof remains open.
The earlier 0008 upkeep attempts hit a missing expectation field; the specification was repaired
and the 0009 trials replace those attempts. Raw failed attempts remain in 0008.

## 4.60.0 re-runs (2026-10-11, claude-opus-5-5, isolated, 1 try, $2.42)

Evidence: `evals/results/2026-10-11-gaps/`. Added as a section; the generated scorecard for this
small run would have replaced the tables above.

| case | without | with | reading |
|---|---|---|---|
| `project-foundation-after-setup` (new) | 1/1 | 1/1 | no difference yet: the plain agent also listed every category |
| `code-history-expired-reason` | not run | 1/1 | WHY.md check now gated; the agent wrote it |
| `scrutinize-unchanged-caller` | not run | 1/1 | used `git worktree add`; the person's checkout stayed put |
| `recall-stale-proof` | not run | 1/1 | still passes with the Context roles table in place of recall's own list |

The scorecard's "opened the skill 2 of 4" counts only Skill-tool calls; the two manual skills
(project-foundation, recall) were opened by reading their SKILL.md, as `actions.txt` shows.

## 4.60.1 re-run (2026-10-11, claude-opus-5-5, 1 try, $1.66)

| case | without | with | reading |
|---|---|---|---|
| `project-foundation-after-setup` (now gates `features.py check` and `.verify-state.json`) | 0/1 | 1/1 | plain wrote FEATURES.md without running the check |

Caveat: the plain arm was not plain. `~/.claude/CLAUDE.md` still loads under
`--setting-sources project,local`, and the agent followed its PHILOSOPHY.md path into this repo's
skills. Evidence: `evals/results/2026-10-11-foundation-skills/`.

## Skill composition regression trials - 2026-10-13

One bounded with-plugin trial per case; phrase grading plus case action checks, no rubric judge.
No no-plugin comparison; context/cost savings and routing reliability remain unmeasured.

| Case | Result | Cost | Seconds |
|---|---|---|---|
| pick-skill-slow-is-a-bug | pass | $0.22 | 36 |
| drive-bug-through-skills | pass | $0.26 | 42 |
| project-foundation-after-setup | fail | $0.30 | 50 |
| onboard-system-stale-architecture | pass | $0.24 | 39 |
| verify-loop-healthy-check | pass | $0.18 | 22 |
| correctness-gate-green-but-wrong | pass | $0.17 | 23 |

Evidence: `results/2026-10-13-1224/`. Foundation failed required helper/evidence actions,
although its report passed. After tightening wording, the replay passed every action check
(including both helpers and retained verification state), but hit the 90-second timeout:
overall not passed, cost unavailable. Evidence: `results/skill-composition-foundation-replay/`.
The first batch reported $1.37 total; unavailable replay usage is not zero cost.
Helper checks: 485 tests passed; final standalone checks 8/8; catalog check passed.

## P02 application recipe replay — 2026-10-13

One bounded with-skill replay of verify-loop-make-it-verified: **0/1 overall**, report 1/1,
skill loaded 1/1; outcome discrimination passed, baseline and final strict green failed.
Model claude-opus-5-5; $0.26, 35 seconds. No baseline arm or reliability claim.
[Retained scorecard](../work/p02/replay-scorecard.md),
[raw evidence](results/p02-replay/verify-loop-make-it-verified/with-1/result.json),
[P02 application trials and limits](../work/p02/evidence.md).

## P04 bounded benchmark-validity trials (2026-10-13)

Baseline with/without: 5/5 each. After: with 4/5, without 5/5; final with replay 4/5. Phrase scorer missed correctly rejected zero-work output in both with reports. Manual reading confirms all five findings; procedure remains partial: final replay opens the reference and sizes full sampling from variation but chooses an arbitrary 20-pair pilot. No reliability or improvement claim. Evidence and limits: [P04](../work/p04/evidence.md).
