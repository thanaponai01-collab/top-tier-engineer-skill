# P07 running artifact identity evidence

Updated: 2026-10-13, Asia/Bangkok. Local implementation and bounded validation were authorized by
`/drive implement p07`. No release or version bump was authorized. P07 is implemented and verified
for the bounded cases below; reliability beyond this single replay remains unmeasured.

## Implementation

- `skills/verify-loop/VERIFY_FORMAT.md` says a Run doctor for a build-sensitive service should compare
  the process's loaded source/build identity and material runtime settings with the expected checkout.
  It covers dirty source, configuration, flags, roles, mocks, mismatch output and verifier receipts.
- `skills/verify-loop/SKILL.md` routes doctor identity work to that guidance and requires reusable
  VERIFY.md instructions and reporting of a healthy stale process with its identity mismatch.
- `tests/test_p07.py` runs a real local HTTP service. It covers unchanged identity and same-HEAD dirty
  source, changed build config digest, flags, role and mocks against a healthy old process.
- `evals/cases/p07-running-artifact-identity` independently replays unchanged identity and rejects
  stale source, build config, flags, role and mocks. Its reference grader rejects the bad report and
  accepts both good reports; the task prompt does not contain the grader's answer phrases.

## Evidence and unresolved checks

- Focused P07 tests passed: `python -m unittest discover -s tests -p test_p07.py` (6 tests).
- Grader calibration passed: `python -m unittest discover -s tests -p test_evals.py` (44 tests).
- The isolated replay passed in both arms. The clean baseline and skill report passed the meaning
  judge; the skill run also passed the independent live replay and action-scope checks. One run per
  arm is a smoke trial, not a reliability or comparative-benefit claim. Raw output is retained in
  `evals/results/p07-run2/`; two earlier failed skill attempts remain in `evals/results/p07-replay/`.
- The full repository suite passed (500 tests), and `python tools/catalog.py --check` passed (36
  skills; listing 4993/5000 characters). The completed current-input gate is `RUN.json`; rejected
  drafts and the earlier oracle-changed run remain preserved under `work/runs/RUN.p07-*.json`.

## Scope and limits

The controlled service covers source content, the config digest, flags, role and mock list on this
Python host. It does not establish that every project's doctor reports every material input. Wider
reliability sampling and other application hosts remain unmeasured.
