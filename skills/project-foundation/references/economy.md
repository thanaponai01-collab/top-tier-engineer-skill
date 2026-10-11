# Economical onboarding delegation

Use delegation only when it reduces total work. The coordinator owns the setup, final documents,
and verification; workers gather bounded evidence in parallel.

## Start with a deterministic inventory

Before delegating, inspect the project instructions, repository/package boundaries, manifests,
existing setup and architecture documents, and available check commands. Record the selected scope
and paths so workers do not repeat discovery. For a small project or a single clear setup path, do
the work in one pass without delegation.

## Delegate bounded read-only discovery

When there are independent areas, use at most two read-only workers. Choose the cheapest available
configured worker the current host supports; do not claim globally cheapest prices or invent model
IDs. Do not change model-switch settings or use paid services.

Give each worker a distinct path/area assignment and explicit ownership: inspect only those paths,
make no edits, and report relevant source evidence and gaps. Keep excerpts bounded and each report
to 20 lines or fewer. Ask for file and line references, observed facts, unresolved questions, and
the next useful path to inspect. Do not send the same inventory to multiple workers or launch an
agent for each checkpoint.

If delegation is unavailable, continue with one agent and the same scoped inventory. Do not block
setup waiting for workers or repeat a scan merely to confirm a completed inventory.

## Coordinator completes and verifies

The coordinator reconciles worker findings against the selected source paths, then writes or
updates shared architecture and setup documentation once. Architecture notes must include source
paths for claims and describe changes incrementally: current behavior, evidence, and the next
change or unknown. Keep separate areas linked rather than duplicating their findings.

Finally, inspect the selected paths directly and run only meaningful, existing checks for the
chosen scope. Report what was checked, what evidence supports the setup, and any remaining gaps.
Delegated discovery is input to this review, not verification by itself.

## Claude Code worker

The plugin ships agents/setup-reader.md with model: haiku and only Read/Grep/Glob tools.
Invoke the plugin-scoped setup-reader for the assigned discovery area; do not assume built-in
Explore is cheap. Host model overrides/availability may change the resolved model; inspect the
actual selection when observable. Other hosts select their supported economical configured model.
A worker cannot run verification or write shared notes; the coordinator performs those once.
Model/tool fields and plugin agents directory are documented at:
https://code.claude.com/docs/en/sub-agents
No provider pricing comparison or guarantee of the globally cheapest model is implied.
