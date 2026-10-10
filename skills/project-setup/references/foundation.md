# Complete project foundation

Setup prepares every relevant category, with explicit unknowns rather than empty placeholders.
Reuse existing equivalents; selected-package scope and gaps stay visible. Never bootstrap a whole
monorepo just because the user chose one package. Smaller projects can keep detail in root files.

| Category | Owner / default | Required content |
|---|---|---|
| Startup | existing AGENTS.md or CLAUDE.md | goal, intent/work pointers, relevant area links, retrieval/upkeep |
| Intent | BRIEF.md | sourced goal, constraints, decisions, acceptance, unanswered questions |
| Work | BUILD.md | current result/evidence, blockers, one Next and completion check |
| Features | FEATURES.md | discovered entry points, traces, checks, evidence labels, unmapped scope |
| Verification | VERIFY.md and receipts | usable selected recipes, prerequisites, limits, actual results |
| Architecture | docs/architecture.md | small as-is diagram, boundary responsibilities, sourced edges, gaps |
| Commands | docs/commands.md | key launch/check/build/CLI commands, directory, prerequisites, source, ran/not ran |
| Memory | existing records and .project-context/index.sqlite | bounded retrieval, ignored/rebuildable cache |

Architecture and command equivalents use `architecture:` and `commands:` pointers in the startup
block. Feature and verification equivalents use `features:` and `verify:` pointers. Intent/work
retain their existing pointer names. Link all present documents once in reading order; detail is
opened by task. Do not create both AGENTS.md and CLAUDE.md for one host.

Target root summaries: brief 60 lines, work 40, feature/check indexes 50; architecture overview
80 lines and about 15 boxes. Link area detail instead of expanding startup. Preserve unresolved
decisions/work and existing hard budgets. Budget pressure never justifies dropping facts.

## Architecture that can change cheaply

Use arch-map's system/module view for the selected package: entry points, core boundaries, storage,
external dependencies, and one important flow. Cite source paths/lines for edges and mark guesses.
An empty project gets its observed state, intended shape explicitly labelled proposed, and missing
implementation; it cannot have a traced running architecture. Never reconstruct reasons from shape.
Keep supported rationale here or linked WHY/decision records; unknown reasons stay unknown.
Add context-paths metadata for representative boundary inputs, not every implementation file.
Refresh affected edges when ownership, entry wiring, storage or integrations change. Ordinary
internal edits need no diagram rewrite. A path-impact hit calls for inspection, not automatic redrawing.

## Complete coverage without unlimited work

Inventory entry-point families (UI/routes, API, CLI, jobs, integrations) and record applicability.
Trace and verify a requirement-backed vertical path first. On large projects batch by reachable area;
record remaining entry points/counts and next batch. Do not claim all features covered because one
check passed. Missing requirements/prerequisites are blockers, not invented defaults.
Command discovery reads manifests/help/config; do not run deployment, sends, migrations or seeds.
Save purpose and source, not copies of every flag. WHY.md/PLAN.md are created only for real rationale
or a multi-step plan, not to satisfy a filename checklist.

## Helpers and refresh

Run `foundation.py --repo <project> inventory` from the installed project-setup scripts directory.
Use --sources with selected implementation/config paths; it compares the previous setup snapshot
when present. No snapshot means freshness unknown. `check` checks document structure only.
After completing discovery and validation, `remember --sources <paths>` records hashes of selected
inputs/documents in the ignored cache. It does not establish product verification or complete coverage.
Use changed/missing categories to scope the next refresh; inspect worker reports once, write once.
Index the context graph after initial setup; later index only changed context records.
