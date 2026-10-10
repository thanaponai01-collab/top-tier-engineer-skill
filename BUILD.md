# Current build

## Project memory
- Goal: independent skills share bounded, searchable context; files own facts and SQLite indexes them.
- Proof: python -m unittest discover tests -p test_project_context.py; then full suite and live evals.
- Status: implementation built; 444 repository tests passed and 14 focused helper tests passed.
- Evidence: .project-context/full-tests-final.log; evals/PROJECT_MEMORY.md. Changes recorded on codex/project-memory; Git identifies the commit.
- Live evaluation: both arms blocked by Claude session limit; no behavioral pass claimed.
- Decisions: working agent maintains affected records; read-only retrieval; no mandatory database.

## Next
Run both project-memory evaluation cases after Claude usage is available; done when a fresh agent
retrieves sourced state and maintains unfinished work without inventing verification. Compare arms.

## Existing work
- include: work/plugin-baseline.md (existing evidence claims, including uncommitted work; not proof of this change)
