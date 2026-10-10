# Current build

## Project memory
- Goal: independent skills share bounded, searchable context; files own facts and SQLite indexes them.
- Proof: python -m unittest discover tests -p test_project_context.py; then full suite and live evals.
- Status: implementation built; 444 repository tests passed and 14 focused helper tests passed.
- Evidence: .project-context/full-tests-final.log; evals/PROJECT_MEMORY.md. Changes recorded on codex/project-memory; Git identifies the commit.
- Live evaluation: both arms blocked by Claude session limit; no behavioral pass claimed.
- Decisions: working agent maintains affected records; read-only retrieval; no mandatory database.

## Foundation refresh
- Setup now owns all context categories, including architecture/commands and memory by default.
- Onboarding reuses the foundation; a bounded Haiku worker gathers evidence without writing notes.
- Foundation inventory/check/remember preserves equivalents and detects selected-input changes.
- Evidence: 452 repository tests passed; 7 foundation and 15 context tests passed.
- Native skills/agent configuration validates; six live Haiku runs hit the account usage limit.
- Current refresh is recorded on codex/project-memory; behavioral validation remains pending.

## Next
After Claude usage is available, rerun the complete-foundation and existing setup evaluations,
then a bounded onboarding prediction check; done when sourced context and preserved requirements
are demonstrated by actual agent work. Unit/structural passes alone do not establish this.

## Existing work
- include: work/plugin-baseline.md (existing evidence claims, including uncommitted work; not proof of this change)
