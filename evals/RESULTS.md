# Verification workflow evaluation

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
