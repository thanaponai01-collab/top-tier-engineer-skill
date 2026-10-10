# Project intent

Extend the existing independent-skills plugin with bounded, searchable project memory.

## Decisions
- Existing Markdown and structured receipts own facts; SQLite is a rebuildable local index.
- The working agent maintains affected context after authorized tasks; no second agent is needed.
- Entry files remain short; area records preserve unfinished work and current requirements.
- Retrieval is read-only, sourced and bounded; historical evidence is not current proof.
- Existing projects and agents without the helper retain direct file-link access.
- RUN.json remains authoritative for driven execution state.
- Setup prepares the full foundation and searchable context by default; other skills remain usable
  without setup, and small edits do not require a database.
- Architecture is a bounded as-is map refreshed for boundary changes; command notes are source-linked.
- Onboarding reuses setup; bounded read-only workers may use a supported economical model.

## Acceptance
- Missing/corrupt indexes fall back to file retrieval; incremental indexing handles deletion.
- A fresh reader finds goal, completed work, blockers and Next without chat history.
- Repeated unchanged upkeep produces no document edits.
- Behavioral skill evaluation must be reported separately from helper tests.

## Design
- include: skills/project-context/references/memory.md (storage, ownership and retrieval)
- include: skills/project-setup/references/foundation.md (complete setup categories and freshness)
- include: skills/project-setup/references/economy.md (bounded economical discovery workers)
