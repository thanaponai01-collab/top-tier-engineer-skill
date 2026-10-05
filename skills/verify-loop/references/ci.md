# Independent CI execution

Use when asked to add CI verification or generate fresh committed-code evidence. This mode is
optional; ordinary builds and reviews can keep using their existing checks.

## Project inputs

Reuse the project's VERIFY.md and test harness. Commit the spec, test inputs and declared oracles.
Commit one targeted mutation per mapped feature that needs fresh rejection proof, using
[challenge mode](challenge.md). Finish all recipe definitions before collecting evidence.
The plan is a repo-relative JSON file, for example `verification/ci.json`:

```json
[
  {"feature": "Refunds", "mutation": "verification/mutations/refunds.json"}
]
```

Use Python 3.12 or newer and Git. From a clean checkout, invoke the reviewed runner:

```bash
python <skill-base>/scripts/verify.py ci . --plan verification/ci.json --output <outside-checkout>/evidence
```

The helper exports committed files from HEAD into a fresh scratch folder, excludes all local
.verify-state.json files, freezes the check definitions, and runs each planned mutation.
Every planned mutation must be caught. It then runs the full recipe strictly and requires
current green status. Missing feature proof, survivors, harness failures and changed checks
fail the job. A plan cannot import a local baseline or failure receipt.

The archive contains the selected project directory, not ignored files or .git metadata.
Install dependencies through the workflow environment or the recipe's setup commands. Use
temporary local services and fixtures. Git-dependent checks and projects needing files outside
that directory need an adapted harness; report that limitation rather than claiming a pass.

## GitHub Actions

Adapt [the workflow template](../assets/verify.yml) to the project's directory, runtime and plan.
Pin the verifier checkout to a reviewed commit with this CI command; do not fetch a moving main
branch as the verification tool. The template uses read-only checkout permissions, disables
persisted Git credentials, and always uploads evidence. Keep production credentials out of
verification jobs. Use pull_request, not privileged pull_request_target, for candidate execution.

The candidate checkout identifies the actual commit tested. For a pull request this example
tests GitHub's merge commit; it does not claim to test only the head branch. See GitHub's
[event semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
and [workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

The working example is `examples/verify-ci/` and `.github/workflows/verify.yml` in this plugin.
Prove the correct example passes and that a weak check and wrong product fail before adapting it.
The template contains no deploy step. Requesting CI setup authorizes verification, not release.

## Evidence and trust

`report.json` records the candidate commit, project path, input fingerprint, check hashes,
verifier hash, stage results and each challenge. `state.json` contains freshly generated strict
state; `run.log` retains output. Evidence is written outside the source checkout, including
on execution failure. A green report is valid only for that tested commit and those expectations.

Fresh CI execution is stronger than trusting a local receipt. It does not make candidate-authored
tests or workflows independently owned. Protect expected outcomes, workflow files and verifier
pins through repository review rules; changes to those are changes to the proof. Scratch folders
are not an OS sandbox, and hostile checks can access external resources available to the job.
Review and redact logs before publishing artifacts; choose retention appropriate to the project.

## Fit with the existing skills

| Skill | How it uses this evidence |
|---|---|
| build-discipline | Proves a slice with the project's existing checks; CI adds committed-code evidence |
| correctness-gate | Judges oracle quality and coverage; CI executes the recipe without replacing that judgment |
| threat-model, perf-optimize, wire-check | Supplies abuse, performance or reachability checks as ordinary recipe commands |
| senior-review, scrutinize | Reads commit-bound evidence when available; review remains usable without CI |
| safe-release | Consumes verification evidence, then separately proves rollback, rollout and deployed behavior |
| drive | Coordinates the work; RUN.json owns progress while VERIFY.md owns check definitions |

Keep BUILD.md, VERIFY.md and RUN.json in their existing roles. Do not introduce a common protocol
or require a chain of skills. Report CI verdict, tested commit, evidence location and coverage
limits; only mark hosted CI proven after observing its actual run.
