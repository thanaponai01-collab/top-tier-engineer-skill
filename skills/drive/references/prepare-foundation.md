# Prepare project foundation


Prepare the complete working foundation in one command, with bounded discovery and explicit gaps.
Use [the foundation contract](foundation.md) for owned documents and equivalents, and
[the economy policy](economy.md) when independent discovery can use cheaper workers.
Let verify-loop judge behavioral verification. No other skill requires setup.

*Evidence labels: **proven** = you ran it; **traced** = followed through code; **suspected** = neither.*

## Inventory and pre-work

Run the installed scripts/foundation.py --repo <project> inventory before reading broad code.
Select the Git root/package, existing pointers and relevant source paths. No prior snapshot means
freshness unknown; existing filenames alone do not prove current context. Load only references for
missing/stale categories. Inventory once, use at most two bounded discovery workers when useful,
and reconcile their cited evidence before writing shared files once. Single-agent fallback is valid.

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

## Prepare every relevant category

Prepare project context using [the context handoff](context-handoff.md): preserve
existing intent/work documents, or save a brief and current next step when absent. Capture intent
from the owner or documented requirements, marking unknowns explicitly. This also applies to an
empty repo: context can be ready while product verification remains unverified.

Read existing VERIFY.md and FEATURES.md first. Reuse equivalent documents and link them where
possible. Update missing or demonstrably stale setup; preserve manual notes, coverage limits and
expectations. Conflicting expectations are a finding, not permission to match the implementation.

- FEATURES.md (or equivalent): selected behavior, requirement source, real entry point, implementation
  and check paths, evidence status. Mark the map partial. Avoid copying every manifest command.
- VERIFY.md: finished checks for the selected behavior, working directory expressed in commands,
  stable behavioral failure signal, declared expectation inputs and blind spots. Add launch,
  readiness, instance identity and cleanup only when checks require a running application.
- verification/: a targeted product mutation for challenge. Add a CI plan only when CI is requested.
- Ignore local .verify-state.json and private generated evidence using existing ignore conventions.
  Reference secrets by location; never record values in these files.


Also complete the foundation's architecture and command categories. Trace a small as-is map using
`arch-map` when available; without it, write sourced boundaries/edges and explicit unknowns in
Markdown. Keep docs/architecture.md within 80 lines and split complex areas. Record key commands,
working directories, prerequisites and observed/not-run status in docs/commands.md; do not copy
all flags or run external actions. Link supported rationale, not guessed history.
Inventory all relevant entry-point families for the selected package; trace/verify in batches and
record coverage gaps and Next. Empty projects get meaningful observed state and unknowns, not
fictional entry points or empty headings. Intent/work are always prepared; no WHY/PLAN placeholders.

## Validate without repeated checkpoints

For new/stale recipes or evidence, read [verification](verification.md), resolve the
installed verify-loop helper, and complete requirement-backed rejection/baseline/strict proof.
For unchanged inputs, reuse only receipts the verifier establishes as current; setup snapshots
alone do not certify anything. Run selected checks once, not once per document or worker.
Report unverified features, unknown requirements and missing prerequisites separately.
After validation re-read selected setup inputs and compare hashes; update only affected records.
Keep source behavior unchanged unless repair was also requested. A defect blocks readiness, not
useful context preparation. Never weaken checks or infer requirements to obtain a pass.

## Make it discoverable

Use the existing agent instruction file (AGENTS.md, CLAUDE.md or equivalent): it is the one file
every session loads without being asked. Add or refresh one start-here block between
`<!-- start-here -->` and `<!-- /start-here -->`, at most 30 lines: the goal in one line, then links
in reading order to the files actually present (`BRIEF.md` for what the owner wants and the decisions
in force, `BUILD.md` for the next step, `FEATURES.md`, `VERIFY.md` with its coverage boundary and
command, architecture and command documentation), and one line saying a changed decision
replaces its line in the brief or its linked area.
State when to read linked areas and identify equivalent documents with `intent:` and `work:`
pointers. Include one upkeep line: authorized updates refresh affected intent, evidence and Next;
read-only reviews report gaps. Links and one-line summaries only; detail stays in the linked files.
Preserve other instructions and never write a
second block. If no instruction file exists, create one appropriate to the requested agent, not
several. Do not impose a required plugin workflow.

## Searchable project memory

Prepare bounded file-backed memory by default. Read project-context's memory reference and helper
--help when the helper is available. Without it, preserve file links and disclose index unavailable;
context can still be useful. Honor an explicit request to skip indexing.
Reuse current documents and include links. Add one retrieval/upkeep line in the existing startup
block with the installed helper path; ignore .project-context/ using existing conventions.
Add architecture:/commands:/features:/verify: pointers for existing equivalents. Index once on
initial setup; on refresh index only changed context files (rebuild if the cache is missing).
Run structural check. Later upkeep uses index --files for changed context only.
Do not make the index a prerequisite for setup or claim it validates product behavior.

## Optional CI

For requested CI setup, read [CI setup](ci-setup.md). Local readiness and hosted readiness
are separate verdicts. Ordinary setup does not authorize commits, pushes or releases.

## Report

Run foundation.py check, then remember --sources with the selected input paths after completing
discovery/validation; the snapshot is a refresh aid, not verification evidence. If blocked, keep a
useful partial foundation and report gaps instead of recording readiness. Run recall's
`context_budget.py <repo> --check-handoff` as described in the context handoff.
Report context completeness separately from verification readiness; unknown intent stays partial.

List created/refreshed/kept files, runtime/package/working directory, commands actually executed,
selected claim, rejection signal and current verdict. Name missing prerequisites, untested behavior,
manual/check edits and the next actionable step. Local verified requires current strict green;
otherwise report draft, blocked or failed with evidence. Never claim every feature or stack covered.
BUILD.md stays progress evidence and RUN.json stays orchestration state; the memory convention remains optional.

*Test:* refresh a partial recipe without changing product behavior or manual expectations;
reject a deliberate wrong result, pass the original and finish strict green. A second unchanged
setup preserves completed files. Missing prerequisites remain explicit.
