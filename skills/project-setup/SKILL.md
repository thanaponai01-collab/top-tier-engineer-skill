---
name: project-setup
description: >-
  Set up or refresh reusable verification in an existing project across stacks. Discover real commands and entry points, preserve manual documentation, prepare a small project map and VERIFY.md, and validate readiness. Use for onboarding verification in another repo or refreshing stale setup. CI is optional when requested; full system explanation belongs to onboard-system. Manual: run /project-setup.
disable-model-invocation: true
metadata:
  stage: orient
  card: "set a project up: start-here block, VERIFY.md"
---

# Project Setup

Prepare project inputs; let verify-loop execute and judge verification. Other skills remain usable
without setup. The seed is a small map grown from evidence, not a complete inventory supplied by
the user.

*Evidence labels: **proven** = you ran it; **traced** = followed through code; **suspected** = neither.*

## Discover

Read project instructions, specifications, manifests, lockfiles, runtime configuration, test
commands and existing CI. Identify the Git root and selected package working directory. For a
monorepo, select the requested package and trace shared dependencies rather than onboarding all
packages. Follow one user/caller entry point into the actual implementation and existing checks.

Use the existing package manager, pinned runtime and harness. Discover commands from configuration
and run them before calling them working. A manifest identifies a stack, not a valid test command.
Lint, compilation and zero-test success alone do not prove behavior. Use documented dependency
setup where authorized; do not migrate frameworks, rewrite lockfiles or install unrelated tools.
Use disposable local services, never production seeds or deployment scripts.

Choose one requirement-backed behavior and adjacent regression checks. Establish expectations from
specifications or user acceptance criteria, not current code. Ask for a missing requirement while
continuing discovery; leave that behavior unverified. An empty repo supports a plan, not proof.

## Prepare the seed

Prepare project context using [the context handoff](references/context-handoff.md): preserve
existing intent/work documents, or save a brief and current next step when absent. Capture intent
from the owner or documented requirements, marking unknowns explicitly. This also applies to an
empty repo: context can be ready while product verification remains unverified.

Read existing VERIFY.md and FEATURES.md first. Reuse equivalent documents and link them where
possible. Update missing or demonstrably stale setup; preserve manual notes, coverage limits and
expectations. Conflicting expectations are a finding, not permission to match the implementation.

- FEATURES.md, when useful: selected behavior, requirement source, real entry point, implementation
  and check paths, evidence status. Mark the map partial. Avoid copying every manifest command.
- VERIFY.md: finished checks for the selected behavior, working directory expressed in commands,
  stable behavioral failure signal, declared expectation inputs and blind spots. Add launch,
  readiness, instance identity and cleanup only when checks require a running application.
- verification/: a targeted product mutation for challenge. Add a CI plan only when CI is requested.
- Ignore local .verify-state.json and private generated evidence using existing ignore conventions.
  Reference secrets by location; never record values in these files.

Resolve verify-loop from the installed plugin/skill location; do not assume its scripts live in
the target repo. Read its SKILL.md, VERIFY_FORMAT.md and relevant challenge reference and run the
bundled helper's --help. Those files own the exact format and mutation schema. Optional init is a
draft generator; finish the selected recipe instead of announcing readiness with TODOs. Trace
unsupported stacks by hand; zero discovered entries does not mean zero features.

## Validate

Run the behavioral check on the unchanged product. Complete verify-loop's actual rejection proof,
baseline, run --strict and current status with this project as the repo argument. Prefer challenge
for a controlled product mistake in scratch copies, leaving source behavior unchanged. Declare
all tests, fixtures, imported check helpers and expectation files before collecting proof. Every
mapped feature needs its own rejection evidence; one caught mutation does not certify the others.

Repair empty/disconnected checks only when their intended requirement is established, disclose
check edits, and regenerate proof. A discovered product defect blocks readiness unless the user
also requested its repair. Preserve unrelated failures and unmapped tests; never delete or weaken
checks to obtain green. Retain outputs and state rather than writing prose-only proof.

If verify-loop is unavailable, prepare a useful draft and execute existing checks directly.
Report draft / verifier unavailable, not strict verified readiness. Explain which installed skill
or reviewed runner is needed; do not silently fetch a moving runner.

Repeat discovery after validation: re-read the instructions, manifests, selected entry point and
recipe; compare setup-file hashes from the first completed pass. Re-running checks alone is not
the second setup pass. An unchanged setup leaves completed files unchanged; reuse
only current evidence. Changed inputs require updating affected recipes and regenerating stale
proof. Compare original/final files, confirm source behavior remains unchanged, and disclose edits.

## Make it discoverable

Use the existing agent instruction file (AGENTS.md, CLAUDE.md or equivalent): it is the one file
every session loads without being asked. Add or refresh one start-here block between
`<!-- start-here -->` and `<!-- /start-here -->`, at most 30 lines: the goal in one line, then links
in reading order to the files actually present (`BRIEF.md` for what the owner wants and the decisions
in force, `BUILD.md` for the next step, `FEATURES.md`, `VERIFY.md` with its coverage boundary and
command), and one line saying a changed decision replaces its line in the brief or its linked area.
State when to read linked areas and identify equivalent documents with `intent:` and `work:`
pointers. Include one upkeep line: authorized updates refresh affected intent, evidence and Next;
read-only reviews report gaps. Links and one-line summaries only; detail stays in the linked files.
Preserve other instructions and never write a
second block. If no instruction file exists, create one appropriate to the requested agent, not
several. Do not impose a required plugin workflow.

## Optional CI

For requested CI setup, read [CI setup](references/ci-setup.md). Local readiness and hosted readiness
are separate verdicts. Ordinary setup does not authorize commits, pushes or releases.

## Report

Run recall's `context_budget.py <repo> --check-handoff` as described in the context handoff.
Report context completeness separately from verification readiness; unknown intent stays partial.

List created/refreshed/kept files, runtime/package/working directory, commands actually executed,
selected claim, rejection signal and current verdict. Name missing prerequisites, untested behavior,
manual/check edits and the next actionable step. Local verified requires current strict green;
otherwise report draft, blocked or failed with evidence. Never claim every feature or stack covered.
BUILD.md stays progress evidence and RUN.json stays orchestration state; no shared protocol is added.

*Test:* refresh a partial recipe without changing product behavior or manual expectations;
reject a deliberate wrong result, pass the original and finish strict green. A second unchanged
setup preserves completed files. Missing prerequisites remain explicit.
