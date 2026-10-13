# P07 running artifact identity evidence

Updated: 2026-10-13, Asia/Bangkok. Local implementation and bounded validation were authorized by
`/drive implement p07`. No release or version bump was authorized. The current recorded drive run is
failed; P07 is implemented, but its behavior and repository gates are not complete.

## Implementation

- `skills/verify-loop/VERIFY_FORMAT.md` says a Run doctor for a build-sensitive service should compare
  the process's loaded source/build identity and material runtime settings with the expected checkout.
  It covers dirty source, configuration, flags, roles, mocks, mismatch output and verifier receipts.
- `skills/verify-loop/SKILL.md` routes doctor identity work to that guidance and requires reusable
  VERIFY.md instructions and reporting of a healthy stale process with its identity mismatch.
- `tests/test_p07.py` runs a real local HTTP service. It covers unchanged identity and same-HEAD dirty
  source, flags, role and mocks against a healthy old process.
- `evals/cases/p07-running-artifact-identity` includes an independent live replay for those cases.

## Evidence and unresolved checks

- Focused P07 tests passed: `python -m unittest discover -s tests -p test_p07.py` (5 tests).
- `python tools/catalog.py --check` passed (36 skills; listing 4993/5000 characters).
- The clean baseline passed. Skill attempts produced report/replay passes but failed workdir scope
  checks because the allowlist omitted helper files, including `identity_check.py`. The failed attempts
  remain under `evals/results/p07-replay/` and `evals/results/p07-final/`.
- The behavior gate did not pass. Correcting the allowlist changed a frozen oracle; the run helper
  rejected the changed oracle hash. `RUN.json` and preserved failed run records document this stop.
  The scorecard currently shows 1/1 baseline and 0/2 skill, so it does not support a benefit claim.
- The full unit suite ran 499 tests and failed two checks: BUILD.md exceeded its 40-line startup cap,
  and the P07 prompt included an answer phrase. BUILD.md was shortened; the prompt no longer has the
  answer token, but the current grader references still fail calibration. The full suite has not passed.
- The successful skill report claim from an earlier draft was incorrect; no skill attempt passed all
  workdir gates. The verifier strict-green behavior also remains unproven.

## Scope and limits

The controlled service covers source content plus tested flags, role and mock list on this Python host.
It does not establish that every project's doctor reports every material input. P07 remains incomplete
until a revised immutable run validates the behavior case, grader calibration passes, and the full
repository suite passes.
