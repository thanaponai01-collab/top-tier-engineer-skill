# P08 standalone use and skill handoffs

Updated: 2026-10-13, Asia/Bangkok. Local implementation and bounded evaluation were authorized by
`/drive implement p08`; no release or version bump was authorized. Implementation is complete;
RUN.json owns the final repository gate.

## Implementation

- `pick-skill` now states the composition rule: skills can be used independently, while workflows
  add only conditional handoffs. Missing skills use the caller's fallback or bounded direct work
  with the missing capability/evidence reported.
- `drive` applies that same fallback rule. `project-foundation` now describes its conditional
  Drive/onboarding callers; `onboard-system` retains a direct route when foundation is unavailable.
- Cross-skill references state the local fallback or limit for build and maintenance context upkeep,
  setup/overnight routing, project update, and architecture mapping. Nine `verify-loop` handoff
  owners retain a fallback or explicit limit.
- `work/p08/check_content.py` checks those nine verification handoffs plus nine other cross-skill
  paths. It verifies documentation shape, not live compliance.

## Behavior evidence

The same one-line calculator fixture and prompt were used before and after skill edits. Trials used
Claude Sonnet 5.5, a $2 per-run cap, and meaning plus action grading.

| Trial | Without | With | Cost | Elapsed |
|---|---:|---:|---:|---:|
| Baseline, before skill edits | 1/1 passed | 1/1 passed | $0.15 | 27.2s |
| Post-edit replay, before final RUN replay | 2/2 passed | 2/2 passed | $0.29 | 53.1s |

Every arm fixed `base - fee` to `base + fee`, reported `12`, and passed the existing unit test with
exit 0. The with-skills transcripts read `pick-skill`, skipped foundation/verify-loop setup, and
passed their action gates. Since baseline already passed, no behavior improvement is claimed. Raw
baseline: `evals/results/2026-10-13-1804/`; post-edit replay: `evals/results/p08-final/`; scorecard:
`evals/RESULTS.md`.

## Verification and limits

- Content audit: `python work/p08/check_content.py` passed (9 verify-loop handoffs; 9 other paths).
- Initial repository proof passed: `python -m unittest discover tests` (500 tests) and `python tools/catalog.py --check` (36 skills). `git diff --check` is clean. The required RUN.json finish replay remains.
- Missing-skill behavior is documented and structurally checked, but no live trial removed a skill
  from the staged plugin. Broader behavior and reliability remain unmeasured.
- The first draft run was preserved as `work/runs/RUN.p08-contract-revised.json` after expanding its
  content checker. Its before-edit baseline remains retained for the revised run.
- A later repository gate failure is preserved as `work/runs/RUN.p08-proof-failed.json`. It exposed a
  prompt/grader leak and a 40-line BUILD.md limit. The prompt and fixture stayed unchanged; the
  rubric was narrowed to passing evidence, the baseline was rescored, and BUILD.md is back within
  its limit. The corrected repository gate completed with all checks passing. A final handoff status/format correction is being revalidated by the current RUN.json finish replay.

The next gate also found that `reference/good.md` omitted the planted passing-test evidence even
though both live arms actually ran and passed the unit test. The positive reference now includes
that evidence. Baseline and post-edit results remain in their retained folders; the current scorecard
reports all graded runs and the final RUN replay adds one more pair.
