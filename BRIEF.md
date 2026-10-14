# Project intent

Extend the existing independent-skills plugin with bounded, searchable project memory.

## What this repo is
- A Claude Code plugin of independent engineering skills: `plugin/skills/<name>/SKILL.md`, each one question
  to one procedure, with optional stdlib-only helpers in its own `scripts/`. No skill requires another.
- Where each fact lives (one home per fact; link, do not copy):
  - skill list and one-line cards: each SKILL.md frontmatter; `tools/catalog.py --write` generates
    `CATALOG.md` (what a fresh session sees) and the README table.
  - which skill for which job, flows, the nine-checkpoint Relay: `plugin/skills/pick-skill/SKILL.md`.
  - driven-run state and evidence: `RUN.json` via `plugin/skills/drive`; unattended variant: `drive-overnight`.
  - project-memory convention: `plugin/skills/project-context/references/memory.md`; setup categories:
    `plugin/skills/project-foundation/references/foundation.md`.
  - proof that a skill changes agent behaviour: `evals/` (`cases/`, `RESULTS.md`); helper tests: `tests/`.
  - hooks: `plugin/hooks/hooks.json` (empty by default), opt-in Stop gate in `plugin/hooks/optional.json`; version: `plugin/.claude-plugin/plugin.json`.
- Rules for changing it are in `CLAUDE.md`; `AGENTS.md` points other agents there.

## Decisions
- Drive is the single explicit workflow entry point. All skills are manual-only; default hooks
  are empty and opt-in profiles retain only completion checks. Specialist procedures are
  read on demand, with evidence-based transitions rather than mandatory chains.
- Existing Markdown and structured receipts own facts; SQLite is a rebuildable local index.
- The working agent maintains affected context after authorized tasks; no second agent is needed.
- Entry files remain short; area records preserve unfinished work and current requirements.
- Retrieval is read-only, sourced and bounded; historical evidence is not current proof.
- Any skill can recover missing task context through relevant requirements, work records, code,
  Git history and verification sources; startup exposes a short pointer to that procedure.
- Existing projects and agents without the helper retain direct file-link access.
- RUN.json remains authoritative for driven execution state.
- Setup prepares agent instructions only; project-foundation prepares foundation and searchable context; skills remain usable
  without setup, and small edits do not require a database.
- Context scales through task-conditioned area links, one home per fact, shared-dependency tracing,
  change-driven upkeep and existing placement conventions; setup remains instructions-only.
- Architecture is a bounded as-is map refreshed for boundary changes; command notes are source-linked.
- Onboarding reuses project-foundation; bounded read-only workers may use a supported economical model.

- Skill composition stays task-sized: direct work or one skill first, conditional handoffs,
  scoped references and reuse of current evidence; small tasks do not require setup or a chain.

## Acceptance
- Missing/corrupt indexes fall back to file retrieval; incremental indexing handles deletion.
- A fresh reader finds goal, completed work, blockers and Next without chat history.
- Repeated unchanged upkeep produces no document edits.
- Behavioral skill evaluation must be reported separately from helper tests.

## Design
- include: plugin/skills/project-context/references/memory.md (storage, ownership and retrieval)
- include: plugin/skills/project-foundation/references/foundation.md (complete setup categories and freshness)
- include: plugin/skills/project-foundation/references/economy.md (bounded economical discovery workers)
