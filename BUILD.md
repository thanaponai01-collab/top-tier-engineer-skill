# Current build

## Project memory
- Goal: independent skills share bounded, searchable context; files own facts and SQLite indexes them.
- Proof: python -m unittest discover tests -p test_project_context.py; then full suite and live evals.
- Status: implementation built; 444 repository tests passed and 14 focused helper tests passed.
- Evidence: .project-context/full-tests-final.log; evals/PROJECT_MEMORY.md. Changes recorded on codex/project-memory; Git identifies the commit.
- Live evaluation: both arms blocked by Claude session limit; no behavioral pass claimed.
- Decisions: working agent maintains affected records; read-only retrieval; no mandatory database.

## Foundation refresh
- Earlier setup version owned all context categories, including architecture/commands and memory by default.
- Onboarding reuses the foundation; a bounded Haiku worker gathers evidence without writing notes.
- Foundation inventory/check/remember preserves equivalents and detects selected-input changes.
- Evidence: 452 repository tests passed; 7 foundation and 15 context tests passed.
- Native skills/agent configuration validates; six live Haiku runs hit the account usage limit.
- Current refresh is recorded on codex/project-memory; behavioral validation remains pending.

## Routing revision
- Setup now writes only agent instructions; Drive owns foundation preparation and task upkeep.
- Plugin workers: Sonnet executor and read-only Haiku reader; host support/overrides apply.
- Added setup-only and repository-authority cases plus adversarial evaluation policy.
- One live setup trial passed; adversarial trial rejected publishing but failed diagnosis/order gates.
- Checks: 452 repository tests passed; updated runner tests (47) and native skill/agent validation passed.
- Actual tier routing and cost reduction remain unmeasured; evidence: evals/PROJECT_MEMORY.md.

## Context scaling
- Setup remains instructions-only; foundation, retrieval and upkeep own the five scaling rules.
- Area records reuse existing homes; shared boundary changes expand discovery to actual callers.
- Placement conventions and affected-record cleanup keep context navigable as modules grow.
- Expanded upkeep fixture preserves unrelated invoice work and replaces stale area summaries.
- Checks: 454 repository tests passed; catalog, affected-context and handoff checks passed.
- Test receipt: .project-context/scalable-context-tests.log (local ignored evidence).
- Evidence: evals/results/2026-10-11-0008/ and evals/results/2026-10-11-0009/.
- Live results: foundation with skill passed, without failed; retrieval/upkeep both arms passed.
- Repeat upkeep is requested by the case; this run's report claims no edits on repeat, but its
  action log does not independently demonstrate a separate post-edit re-read.

## Next
Strengthen fresh-reader/repeated-upkeep trials with independent action evidence and larger area
fixtures; done when bounded loading and unchanged second-pass files are demonstrated across runs.

## Existing work
- include: work/plugin-baseline.md (existing evidence claims, including uncommitted work; not proof of this change)
